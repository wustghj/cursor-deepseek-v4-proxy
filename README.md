# 🧠 Cursor DeepSeek V4 Proxy

**彻底解决 Cursor 使用 DeepSeek V4 模型时的 `reasoning_content must be passed back` 错误，同时自动处理限流、模型名无效等问题。**

[![GitHub stars](https://img.shields.io/github/stars/你的用户名/cursor-deepseek-v4-proxy?style=social)](https://github.com/你的用户名/cursor-deepseek-v4-proxy)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 如果你在使用 Cursor 调用 DeepSeek V4 Pro/Flash 时遇到 "Provider returned error: reasoning_content must be passed back" 或 "User API Key Rate limit exceeded"，这个项目就是为你准备的。只需运行一个本地代理，一切恢复正常。

---

## ✨ 特性

- **修复推理链丢失**：自动缓存并回传 `reasoning_content`，支持多轮对话、工具调用、子任务。
- **智能限流**：内置令牌桶，防止免费配额瞬间触发 429 错误。
- **支持流式输出**：不影响 Cursor 的实时反馈体验。
- **一键启动**：Windows / macOS / Linux 下都提供自动化脚本。
- **透明日志**：实时显示请求状态，方便排查问题。
- **无需修改 Cursor 内部文件**，只改一个 Base URL。

---

## 🚀 快速开始（3 步）

### 1. 安装依赖

确保已安装 [Python 3.8+](https://www.python.org/)。然后克隆本项目并安装依赖：

```bash
git clone https://github.com/你的用户名/cursor-deepseek-v4-proxy.git
cd cursor-deepseek-v4-proxy
pip install -r requirements.txt
