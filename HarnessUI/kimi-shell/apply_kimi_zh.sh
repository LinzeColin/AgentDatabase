#!/bin/bash
# Kimi Code 关掉之后再跑这一条：把中文名改动打进 app.asar。
set -e
SHELL_DIR="$HOME/.kimi-code/shell"
APP="$HOME/Applications/Kimi Code.app/Contents/Resources/app.asar"
ASAR="$SHELL_DIR/node_modules/@electron/asar/bin/asar.mjs"
pgrep -f "Kimi Code" >/dev/null && { echo "Kimi 还在跑，先退出再执行"; exit 1; }
cp "$APP" "$APP.bak-$(date +%Y%m%d-%H%M%S)"
node "$ASAR" pack "$SHELL_DIR" "$APP.new"
mv "$APP.new" "$APP"
echo "已打包。启动 Kimi 后菜单和画廊就是全中文。"
