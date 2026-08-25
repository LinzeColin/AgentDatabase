# Your machine

**本机 bootstrap 完成于 2026-08-24（DEV-MACPRO）。此文件不随 skill 更新覆盖。**

- **ComfyUI**：源码安装 `~/ComfyUI-Installs/ComfyUI/ComfyUI`，API `http://127.0.0.1:8188`
- **平台**：darwin · ComfyUI 0.33.2 · Python 3.13.12
- **设备**：mps（type=mps, vram_total=32.0GB）
  - ⚠️ Apple Silicon **统一内存**，不是独立 VRAM。判可用内存必须算 `free + inactive + speculative + purgeable`，
    只看 `Pages free` 会低估 68 倍（实测 0.06GB vs 实际 4.11GB）。
- **启动命令（原样恢复，参数不许改）**：
  ```
  /Users/linzezhang/ComfyUI-Installs/ComfyUI/ComfyUI/.venv/bin/python main.py --output-directory /Users/linzezhang/.douyinops/out --enable-manager --fp32-vae --use-split-cross-attention --disable-smart-memory
  ```
  ⚠️ **绝不能加 `--bf16-unet`** —— SDXL 在 MPS 上会算出 NaN 出纯色废图，而 ComfyUI 仍报 success。
  拉起脚本：`/tmp/start_comfy.py`（双 fork 真脱离，macOS 无 setsid 命令）
- **输出目录**：`~/.douyinops/out`（本机暂存）→ rsync 归档到 SMB `04_素材产线/输出/`
  ⚠️ **不要把 `--output-directory` 指向 /Volumes/share** —— 图算完了才在 SaveVideo 报 PermissionError，白烧算力。
- **GUI 工作流目录**：`~/ComfyUI-Installs/ComfyUI/ComfyUI/user/default/workflows/`
- **本仓自有工作流**：`~/Documents/DouyinOps/02_通用资产/工作流/wan22_5B_ti2v.json`（UI 格式，
  用 `comfy workflow set-slot` + `comfy run` 提交；直接 POST /prompt 会 500，因为不是 API 格式）
  槽位：`56.image` · `6.text`(正) · `7.text`(负) · `55.width/height/length` · `57.fps` · `58.filename_prefix` · `3.cfg/steps/seed`
- **comfy CLI**：`~/.local/share/uv/tools/comfy-cli/bin/comfy`（v1.16.0；`run` 的 `--wait` 不接受值）
- **本机已装模型（实时查，别硬编码）**：
  - `UNETLoader.unet_name`: ['wan2.2_ti2v_5B_fp16.safetensors', 'wan22_fun_5B_inp.safetensors']
  - `UNETLoader.weight_dtype`: ['default', 'fp8_e4m3fn', 'fp8_e4m3fn_fast', 'fp8_e5m2']
  - `CheckpointLoaderSimple.ckpt_name`: ['waiIllustriousSDXL_v170.safetensors']
  - `CLIPLoader.clip_name`: ['umt5-xxl-enc-bf16-conv.safetensors', 'umt5-xxl-enc-fp8_e4m3fn.safetensors', 'umt5_xxl_fp8_e4m3fn_scaled.safetensors']
  - `CLIPLoader.type`: ['stable_diffusion', 'stable_cascade', 'sd3', 'stable_audio', 'mochi', 'ltxv']

## 本机实测的生产配置（仓内已定，不许自己另发明）
| 项 | 值 | 出处 |
|---|---|---|
| 模型 | `wan2.2_ti2v_5B_fp16.safetensors` | 视频产线总则 |
| 步数 / CFG | **20 步 / cfg=1.0** | cfg 1/1.5 干净、3 劣化、**5 全崩**（2026-08-22 实测） |
| 规格 | 704×1280 · 33 帧 · **24fps**（5B TI2V 原生） | 七卡 §一 + Wan 官方配方 |
| 循环 | 乒乓 ×2 → ≈5.5 秒 | 33帧=1.375秒，ffmpeg 补，零额外算力 |
| 角色锚定 | 704×1280×33帧 = **99.2%**（121帧崩到 55.9%） | 高分辨率+长帧数凑一起才超锚定范围 |
| 单条耗时 | ≈23 分钟（VAE 解码约 12 分钟是固定开销，压不动） | — |

## 判任务死活（MPS 专用）
**不能看 RSS 和瞬时 CPU%** —— MPS 权重在 Metal buffer 里不计入 RSS，正常跑的任务看起来是 RSS 0.1GB / CPU 1.5%。
正确判据：`ps -o time= -p <pid>` 隔 20 秒比两次，累计 CPU 时间在涨 = 在算。
