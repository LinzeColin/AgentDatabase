#!/bin/sh
set -eu
cd -- "$(dirname -- "$0")"
python3 START_HERE.py install
printf '\n安装命令已完成。\n'
if [ -t 0 ]; then
  printf '按回车关闭。\n'
  read -r answer
fi
