import json
import hashlib
import time
import threading
import logging
import sys
import requests
from flask import Flask, request, Response, stream_with_context

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
UPSTREAM_URL = "https://api.deepseek.com/v1/chat/completions"

# ===== 令牌桶限流 =====
class TokenBucket:
    def __init__(self, rate, capacity):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_time = time.monotonic()
        self.lock = threading.Lock()
    def consume(self):
        with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_time
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_time = now
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False

bucket = TokenBucket(rate=5/60.0, capacity=5)

# ===== 缓存：键 = 去掉 reasoning_content 后的 assistant 消息序列化 =====
reasoning_cache = {}

def msg_key(msg: dict) -> str:
    """生成不包含 reasoning_content 的完整消息体的哈希"""
    # 复制一份，防止修改原消息
    m = {k: v for k, v in msg.items() if k != 'reasoning_content'}
    # 标准化序列化
    payload = json.dumps(m, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(payload.encode()).hexdigest()

def strip_image_content(messages):
    """
    遍历消息，移除所有 'image_url' 类型的内容块。
    如果某条消息的 content 是数组，过滤后只保留 'text' 块；
    如果过滤后数组为空，则替换为一个占位文本，避免模型收到空 content。
    """
    for msg in messages:
        content = msg.get('content')
        if not isinstance(content, list):
            continue  # 字符串 content 无需处理

        text_parts = [
            part for part in content
            if part.get('type') == 'text'
        ]

        if not text_parts:
            # 所有内容都被过滤掉了（例如纯图片消息）
            msg['content'] = "[用户发送了一张图片，但当前模型不支持图片输入，请以文本方式回应]"
        else:
            # 保留文本块，移除图片块
            msg['content'] = text_parts
    return messages

@app.route('/v1/chat/completions', methods=['POST'])
@app.route('/chat/completions', methods=['POST'])
def chat_completions():
    # 限流等待
    while not bucket.consume():
        time.sleep(0.5)

    body = request.get_json(force=True)
    model = body.get('model', 'unknown')
    msg_count = len(body.get('messages', []))
    logger.info(f"Received {msg_count} messages, model={model}")

    # ----- 补全历史 assistant 消息的 reasoning_content -----
    if 'messages' in body:
        for idx, msg in enumerate(body['messages']):
            if msg.get('role') == 'assistant' and 'reasoning_content' not in msg:
                key = msg_key(msg)
                if key in reasoning_cache:
                    msg['reasoning_content'] = reasoning_cache[key]
                    logger.info(f"→ Patched reasoning for msg[{idx}]")
                else:
                    msg['reasoning_content'] = ""
                    logger.info(f"→ No cached reasoning for msg[{idx}], set empty. key={key[:8]}...")

    # ----- 过滤掉所有 image_url 内容块 -----
    body['messages'] = strip_image_content(body.get('messages', []))
    body['stream'] = True
    headers = {
        "Authorization": request.headers.get("Authorization", ""),
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }

    # 转发请求（带 429 重试）
    resp = None
    for attempt in range(3):
        try:
            resp = requests.post(
                UPSTREAM_URL,
                headers=headers,
                json=body,
                stream=True,
                timeout=120
            )
        except Exception as e:
            logger.error(f"Request exception: {e}")
            break

        if resp.status_code == 429:
            logger.warning("Got 429, retrying in 3s...")
            time.sleep(3)
        else:
            break

    # ----- 优化错误返回：统一 JSON 格式，针对图片错误给出友好提示 -----
    if resp is None or resp.status_code != 200:
        if resp is not None:
            try:
                err_data = resp.json()
                err_msg = err_data.get('error', {}).get('message', '')
                # 如果错误仍与图片相关（双重保险），给出更明确的提示
                if 'image_url' in err_msg:
                    friendly_error = {
                        "error": {
                            "message": "当前模型不支持图片输入，请移除图片内容或使用支持视觉的模型（如 deepseek-chat）。",
                            "type": "unsupported_media",
                            "code": "image_not_supported"
                        }
                    }
                    logger.warning("Upstream image error, returning friendly message.")
                    return Response(
                        json.dumps(friendly_error, ensure_ascii=False),
                        status=400,
                        mimetype='application/json'
                    )
            except:
                pass

        # 通用错误处理：统一返回 JSON，避免透传上游可能不规范的错误体
        error_body = {
            "error": {
                "message": "上游服务返回错误，请稍后重试。",
                "type": "upstream_error",
                "code": str(resp.status_code) if resp else "502",
                "detail": (resp.text[:200] if resp else "no response")
            }
        }
        logger.error(f"Upstream error {resp.status_code if resp else 'None'}, detail: {resp.text[:500] if resp else 'None'}")
        return Response(
            json.dumps(error_body, ensure_ascii=False),
            status=resp.status_code if resp else 502,
            mimetype='application/json'
        )

    # ===== 流式处理：完整收集 content 和 tool_calls =====
    def generate():
        collected_content = ""
        collected_reasoning = ""
        tool_calls = {}  # index -> {id, function_name, arguments}

        for line in resp.iter_lines(decode_unicode=True):
            yield line + '\n'
            if not line.startswith('data:'):
                continue
            data_str = line[5:].strip()
            if data_str == '[DONE]':
                break
            try:
                chunk = json.loads(data_str)
                delta = chunk['choices'][0].get('delta', {})
                # 推理内容
                if 'reasoning_content' in delta:
                    collected_reasoning += delta['reasoning_content']
                # 普通文本
                if 'content' in delta:
                    collected_content += delta['content']
                # 工具调用（增量累积）
                if 'tool_calls' in delta:
                    for tc in delta['tool_calls']:
                        idx = tc.get('index', 0)
                        if idx not in tool_calls:
                            tool_calls[idx] = {
                                'id': '',
                                'function': {'name': '', 'arguments': ''}
                            }
                        if 'id' in tc:
                            tool_calls[idx]['id'] = tc['id']
                        if 'function' in tc:
                            func = tc['function']
                            if 'name' in func:
                                tool_calls[idx]['function']['name'] += func['name']
                            if 'arguments' in func:
                                tool_calls[idx]['function']['arguments'] += func['arguments']
            except Exception:
                pass

        resp.close()

        # 构建最终的 assistant 消息结构（与 Cursor 发送的一致）
        final_msg = {}
        if collected_content:
            final_msg['content'] = collected_content
        else:
            final_msg['content'] = None  # 或 ""
        if tool_calls:
            # 按 index 排序，去除临时 id
            sorted_tc = [tool_calls[k] for k in sorted(tool_calls.keys())]
            final_msg['tool_calls'] = sorted_tc
        # 如果有 reasoning，缓存（key 不含 reasoning）
        if collected_reasoning:
            cache_key = msg_key(final_msg)
            reasoning_cache[cache_key] = collected_reasoning
            logger.debug(f"Cached reasoning for key={cache_key[:8]}...")

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
        }
    )

@app.route('/v1/models', methods=['GET'])
@app.route('/models', methods=['GET'])
def models():
    headers = {"Authorization": request.headers.get("Authorization", "")}
    r = requests.get("https://api.deepseek.com/v1/models", headers=headers)
    logger.info(f"Models endpoint: {r.status_code}")
    return Response(r.content, status=r.status_code, headers=dict(r.headers))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000, debug=False)