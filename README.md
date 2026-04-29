# 🧠 Cursor DeepSeek V4 Proxy

> **一键修复 Cursor 使用 DeepSeek V4 时的 `reasoning_content` 错误，告别 `Rate limit exceeded`，让代理 Agent 模式稳定运行。**

[![GitHub stars](https://img.shields.io/github/stars/你的用户名/cursor-deepseek-v4-proxy?style=social)](https://github.com/你的用户名/cursor-deepseek-v4-proxy)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📌 你能用这个项目解决什么问题？

如果你在 Cursor 中调用 DeepSeek V4（Pro / Flash）时，频繁遇到下面任意一种错误：

- `Provider returned error: The reasoning_content in the thinking mode must be passed back to the API.`
- `User API Key Rate limit exceeded`（明明配额还剩很多却报错）
- `AI Model Not Found: deepseek-v4-pro`（后台任务报模型名无效）
- 聊天第一轮正常，第二轮就开始报错、中断

**不用再折腾了，跟着本指南走 5 分钟就能彻底解决。**

---

## ✨ 核心功能

- ✅ **自动缓存 & 回传思维链**：再也不会因为 `reasoning_content` 缺失而报错  
- ✅ **智能限流**：内置令牌桶，防止突发的并发请求打满免费额度  
- ✅ **支持流式输出**：不影响 Cursor 的打字机效果  
- ✅ **一键启动脚本**：Windows / macOS / Linux 通用，双击即可运行  
- ✅ **透明日志**：终端会实时显示请求状态，方便排错  
- ✅ **零侵入**：不需要修改 Cursor 程序文件，只改一个 Base URL

---

## 🖥️ 适用环境

| 操作系统 | 支持 |
| -------- | ---- |
| Windows 10 / 11 | ✅ |
| macOS | ✅ |
| Linux | ✅ |

唯一需要的额外环境：**Python 3.8 或更高版本**（绝大部分电脑都已经装过）。

---

## 🚀 超详细三步上手（小白照做就行）

### 第一步：下载项目并安装依赖

1. 打开本页面，点击右上角绿色的 `Code` 按钮，选择 `Download ZIP`，下载后解压到任意目录（不要放在中文路径里）。
2. 进入解压后的文件夹，在地址栏输入 `cmd` 并回车，打开命令提示符。
3. 在命令提示符里执行以下命令：

```bash
pip install -r requirements.txt
如果提示 pip不是内部命令，说明你的 Python 没有装好，请先去 python.org 下载安装，安装时务必勾选 Add Python to PATH。

安装完成后，窗口输出类似 Successfully installed ... 就成功了。

第二步：启动本地代理 + 隧道
你需要一个 Cloudflare 隧道来生成公网地址（免费，不需要注册）。

🪟 Windows 用户
在项目文件夹里找到 cloudflared-windows-amd64.exe，如果没有，点此下载，下载 cloudflared-windows-amd64.exe 文件，放到项目文件夹内。

双击 start_proxy.bat。

会弹出两个窗口：一个是本地代理，一个是隧道。不要关闭它们。

在隧道窗口中，你会看到一串 https://xxx.trycloudflare.com 的地址，把它复制下来。

🍎 macOS / Linux 用户
在终端中进入项目目录，运行：

bash
bash start_proxy.sh
终端会先启动代理，再启动隧道。稍等片刻，你会看到 https://xxx.trycloudflare.com 地址。

复制这个地址。

⚠️ 注意：隧道地址是临时生成的，每次重启都会变化。只要你不关闭窗口，地址就一直有效。

第三步：配置 Cursor
打开 Cursor 设置（Ctrl+Shift+P → 输入 Cursor Settings，或直接点左下角齿轮 → Settings）。

选择 Models 选项卡。

在 “Override OpenAI Base URL” 输入框中，粘贴刚才复制的隧道地址，并在末尾加上 /v1，像这样：

text
https://xxxxxx.trycloudflare.com/v1
在 API Key 输入框里填写你的 DeepSeek API Key（从 DeepSeek 开放平台 获取）。

关闭设置窗口，彻底退出 Cursor 再重新打开。

现在，你可以正常聊天、使用 Agent 模式了，那些恼人的错误不会再出现！

🛡️ 修复 “Model name not valid: deepseek-v4-pro” 错误
如果你在后台任务（如 Apply）时看到这个错误，按下面方法操作一次即可：

在 Cursor 中按 Ctrl+Shift+P，输入 Preferences: Open User Settings (JSON)，回车。

在打开的大括号 {} 内，添加以下配置（记得替换你的隧道地址和 API Key）：

json
"cursor.models": {
    "deepseek-v4-pro": {
        "provider": "openai",
        "apiBase": "https://xxxxxx.trycloudflare.com/v1",
        "apiKey": "你的DeepSeek API Key"
    }
}
保存文件，完全退出 Cursor，再重新打开即可。

❓ 常见问题
<details> <summary>🔁 隧道地址变了怎么办？</summary>
每次启动代理时，隧道地址都是随机生成的。如果你重启了电脑或关闭了隧道窗口，地址就会变化。
此时只需要：重新运行 start_proxy.bat / start_proxy.sh，获取新地址，更新到 Cursor 的 Base URL 里（以及 settings.json 里，如果配置过的话）。
项目文件夹不用变，代理代码是固定的。

</details><details> <summary>💸 还是会提示 Rate limit exceeded？</summary>
免费的 DeepSeek API 每分钟请求次数有限（通常 3～5 次），Agent 模式可能瞬间触发。
你可以打开 proxy.py，找到这一行：

python
bucket = TokenBucket(rate=5/60.0, capacity=5)
把 5 改成更小的数字，比如 3，保存后重启代理。这样代理会强制减慢请求速度，避免触发 429。

</details><details> <summary>🧪 代理会影响模型智商吗？</summary>
在极少数子任务中，代理可能会因为无法匹配思维链而补一个空字符串，导致模型丢失之前的推理过程。
实际测试中，绝大多数对话（包括复杂代码分析）几乎感觉不到差异。相比彻底无法使用，这个代价完全可以接受。

</details><details> <summary>🚫 必须用隧道吗？能不能直接连 localhost？</summary>
Cursor 出于安全限制，禁止客户端访问 localhost 等私有网络地址，所以必须通过隧道将本地端口映射到公网。
本项目使用的 Cloudflare Tunnel 完全免费，无需注册，也不存储任何数据，请放心使用。

</details><details> <summary>🔄 用其它隧道工具可以吗？</summary>
当然可以，比如 ngrok。启动 ngrok 后把得到的 https://xxx.ngrok.io 地址同样添加 /v1 填到 Cursor 的 Base URL 即可。

</details><details> <summary>🪟 代理窗口一直开着很烦，能隐藏吗？</summary>
Windows 用户可以直接将 start_proxy.bat 的快捷方式放到启动文件夹，让它开机自动运行。
或者使用 nssm 等工具把 python proxy.py 注册为系统服务，完全无窗口。

</details>
⚙️ 高级自定义
调低限流：如前所述，修改 proxy.py 中的 rate 数值。

固定隧道域名：如果你有自己的域名，可以创建 Cloudflare 命名隧道，将其绑定到固定域名。这一步稍复杂，可自行搜索 cloudflared tunnel persistent。

更换上游 API：如果你用其它兼容 OpenAI 接口的 API，可以修改 proxy.py 开头的 UPSTREAM_URL 地址。

