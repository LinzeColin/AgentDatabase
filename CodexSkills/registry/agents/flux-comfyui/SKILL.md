---
name: flux
description: Flux.2 Dev 本地文生图/图生图。触发：/flux、文生图、图生图、AI绘图、AI生成图片、flux生成、生成图片、画一张、画个、用flux、生成一张。用户说「画个xx」「生成一张xx的图」「把这张图变成xx风格」等。
---

# Flux.2 Dev 本地生图

通过本地 ComfyUI + Flux.2 Dev 模型生成图片，支持文生图和图生图。

## 首次使用

skill 会检测 `config.local.json`，不存在时自动从 `config.example.json` 复制并提示你编辑 **两项必填**：

| 配置项 | 说明 |
|--------|------|
| `comfyui_url` | ComfyUI 服务地址，默认 `http://localhost:8188` |
| `comfyui_dir` | ComfyUI 安装目录，例如 `E:\ComfyUI` |

其余项（尺寸、步数、输出目录）有默认值，可直接用。

## 执行脚本

> **重要：** 写临时脚本到 `tempfile.gettempdir()/flux/` 目录，不要写 skill 目录或当前工作目录。所有路径通过 skill 目录动态解析。

```python
import sys, json, subprocess, os, tempfile

SKILL_DIR = r"<SKILL_DIR>"   # skill 目录，运行时替换
sys.path.insert(0, SKILL_DIR)

from comfyui_client import ComfyUIFluxClient, check_comfyui_available, launch_comfyui, wait_for_comfyui

# 1. 加载本地配置
cfg_path = os.path.join(SKILL_DIR, "config.local.json")
if not os.path.exists(cfg_path):
    # 首次使用：从模板创建
    import shutil
    example = os.path.join(SKILL_DIR, "config.example.json")
    shutil.copy(example, cfg_path)
    print(f"已创建 {cfg_path}，请编辑后重试")
    print("必填项：comfyui_dir（ComfyUI 安装目录）")
    sys.exit(1)

with open(cfg_path, "r") as f:
    cfg = json.load(f)

server_url = cfg.get("comfyui_url", "http://localhost:8188")
comfyui_dir = cfg.get("comfyui_dir", "")
output_dir = cfg.get("output_dir", os.path.join(SKILL_DIR, "outputs"))
width = cfg.get("flux_width", 1024)
height = cfg.get("flux_height", 768)
steps = cfg.get("flux_steps", 20)
guidance = cfg.get("flux_guidance", 3.5)

# 2. 探活 / 自动启动 ComfyUI
if not check_comfyui_available(server_url):
    if comfyui_dir and os.path.isdir(comfyui_dir):
        print("ComfyUI 不在线，正在启动...")
        launch_comfyui(comfyui_dir, server_url)
        if not wait_for_comfyui(server_url, timeout=180):
            print("ComfyUI 启动超时，请手动检查")
            sys.exit(1)
        print("ComfyUI 已就绪")
    else:
        print("ComfyUI 不在线，且 comfyui_dir 未配置或不存在")
        print(f"请编辑 {cfg_path} 设置 comfyui_dir")
        sys.exit(1)

# 3. 生成
client = ComfyUIFluxClient(server_url, output_dir=output_dir)

# === 文生图 ===
output_path = client.generate(
    prompt="PROMPT_HERE",
    width=width, height=height,
    steps=steps, guidance=guidance,
)

# === 图生图（需要时取消注释，注释掉上面的文生图调用）===
# output_path = client.generate(
#     prompt="PROMPT_HERE",
#     width=width, height=height,
#     image_paths=[r"FULL_PATH_TO_REF.png"],
#     steps=steps, guidance=guidance,
# )

print(f"图片已保存: {output_path}")

# 4. 复制路径到剪贴板（Windows）或打印（其他平台）
if sys.platform == "win32":
    subprocess.run(["clip.exe"], input=output_path.strip().encode("utf-16-le"), check=True)
    print("（路径已复制到剪贴板）")
```

## 参数说明

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `prompt` | str | 必填 | 英文提示词更精确，中文自动翻译 |
| `width` | int | 1024 | 宽度 |
| `height` | int | 768 | 高度 |
| `image_paths` | list | None | 传值=图生图，None=文生图 |
| `steps` | int | 20 | 采样步数 1~50 |
| `guidance` | float | 3.5 | CFG 引导度 1.0~10.0 |
| `seed` | int | 随机 | 固定可复现 |

## 用户意图解析

- **prompt**：用户自然语言描述 → 翻译为英文
- **参考图**：「把这张图」「以这张图为参考」「基于这个图片」「图生图」+ 上下文有图片路径 → 图生图模式
- **尺寸**：「横版」→1024x768、「竖版」→768x1024、「方形」→1024x1024；也可指定具体像素
- **步数**：「精细一点」「高质量」「多步」→25~30、「快速」→12~15

## 文件结构

```
.claude/skills/flux/
├── SKILL.md              # 本文件
├── comfyui_client.py     # 核心客户端（自包含，不依赖 chat_gui.py）
├── config.example.json   # 配置模板（可提交 git）
├── config.local.json     # 本地配置（不提交 git）
└── outputs/              # 生成图片输出目录
```

## 临时文件规范

- 所有临时脚本写入 `tempfile.gettempdir()/flux/`，操作系统自动清理
- 不主动删除临时文件
- 不在 skill 目录或用户项目目录写临时文件
