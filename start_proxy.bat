@echo off
title DeepSeek V4 Proxy for Cursor
cd /d "%~dp0"

echo ========================================
echo  Starting DeepSeek V4 Proxy...
echo ========================================
start "ProxyServer" cmd /c "python proxy.py"
timeout /t 3 /nobreak >nul

echo.
echo Starting Cloudflare Tunnel...
echo.
cloudflared-windows-amd64.exe tunnel --url http://localhost:9000

pause