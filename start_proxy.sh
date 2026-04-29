#!/bin/bash
echo "Starting DeepSeek V4 Proxy..."
python3 proxy.py &
sleep 3

echo "Starting Cloudflare Tunnel..."
cloudflared tunnel --url http://localhost:9000