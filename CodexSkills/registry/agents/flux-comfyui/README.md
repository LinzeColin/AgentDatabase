# Flux ComfyUI Skill

Claude Code skill for local image generation using Flux.2 Dev via ComfyUI.

## Requirements

| Component | Details |
|-----------|---------|
| ComfyUI | Portable/installed, with Flux.2 custom nodes |
| Flux.2 Dev models | UNET (~11GB fp8), CLIP (~15GB), VAE (~1GB) |
| GPU | NVIDIA, 8GB+ VRAM (RTX 4060 tested) |
| Upscale model | `4x-UltraSharp.pth` in `models/upscale_models/` (optional) |

## Model Downloads

Place these files in the directories shown under your ComfyUI folder:

| Model | File | Size | Put in | Download |
|-------|------|------|--------|----------|
| UNET (FP8) | `flux2_dev_fp8mixed.safetensors` | ~35.5 GB | `models/diffusion_models/` | [Comfy-Org/flux2-dev](https://huggingface.co/Comfy-Org/flux2-dev/tree/main/split_files/diffusion_models) |
| CLIP (BF16) | `mistral_3_small_flux2_bf16.safetensors` | ~35.6 GB | `models/text_encoders/` | [Comfy-Org/flux2-dev](https://huggingface.co/Comfy-Org/flux2-dev/tree/main/split_files/text_encoders) |
| VAE | `full_encoder_small_decoder.safetensors` | ~1 GB | `models/vae/` | [black-forest-labs/FLUX.2-small-decoder](https://huggingface.co/black-forest-labs/FLUX.2-small-decoder) |
| Upscaler (可选) | `4x-UltraSharp.pth` | ~67 MB | `models/upscale_models/` | [uwg/upscaler](https://huggingface.co/uwg/upscaler) |

> 💡 **显存吃紧？** CLIP 可以换成 FP8 版 `mistral_3_small_flux2_fp8.safetensors`（同样在 Comfy-Org/flux2-dev 仓库），省一半显存。

### 下载命令

```bash
# UNET (35.5 GB)
huggingface-cli download Comfy-Org/flux2-dev split_files/diffusion_models/flux2_dev_fp8mixed.safetensors --local-dir ComfyUI/models/diffusion_models

# CLIP (35.6 GB)
huggingface-cli download Comfy-Org/flux2-dev split_files/text_encoders/mistral_3_small_flux2_bf16.safetensors --local-dir ComfyUI/models/text_encoders

# VAE (~1 GB)
huggingface-cli download black-forest-labs/FLUX.2-small-decoder full_encoder_small_decoder.safetensors --local-dir ComfyUI/models/vae

# Upscaler (67 MB, 可选)
huggingface-cli download uwg/upscaler ESRGAN/4x-UltraSharp.pth --local-dir ComfyUI/models/upscale_models
```

## Installation

1. Copy this folder into `~/.claude/skills/flux/`
2. Restart Claude Code
3. First run will create `config.local.json` — edit your ComfyUI path:
   ```json
   {
     "comfyui_url": "http://localhost:8188",
     "comfyui_dir": "E:\\ComfyUI"
   }
   ```

## Usage

```
/flux a cute orange cat sitting on a cloud
画个赛博朋克城市的夜景
把这张图变成水彩画风格          (attach reference image)
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | str | required | English works best; Chinese auto-translated |
| width | int | 1024 | Image width |
| height | int | 768 | Image height |
| steps | int | 20 | Sampling steps (1-50) |
| guidance | float | 3.5 | CFG guidance scale (1.0-10.0) |
| sampler | str | euler | Sampler: euler, dpmpp_2m, dpmpp_sde, heun, uni_pc |
| scheduler | str | simple | Scheduler: simple, karras, ddim_uniform, sgm_uniform, beta |
| upscale | bool | false | Enable 4× AI upscale (requires 4x-UltraSharp.pth) |

## Features

- **txt2img**: Generate from text prompt
- **img2img**: Generate with reference image
- **AI Upscale**: 4× upscale via ESRGAN (4x-UltraSharp)
- **Sampler/Scheduler selection**: euler/dpmpp_sde/karras etc.
- **Auto-launch ComfyUI**: Starts ComfyUI if not running
- **Progress display**: Shows elapsed time during generation

## File structure

```
.claude/skills/flux/
├── SKILL.md
├── comfyui_client.py
├── config.example.json
├── config.local.json    (gitignored)
└── outputs/             (gitignored)
```
