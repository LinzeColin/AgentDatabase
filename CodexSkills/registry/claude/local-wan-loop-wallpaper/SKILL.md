---
name: local-wan-loop-wallpaper
description: 用本机 ComfyUI + Wan2.2-Fun-5B-InP 把一张静态壁纸变成无缝循环的待机短视频（首尾帧同图法）。Use when 要出循环/待机壁纸、要给抖音做零剪辑口的动态壁纸、静态图已验收要接动效、或排查「循环点看得出来 / 视频打不开 / 人物变形」。上游是 local-sdxl-wallpaper（静态图来源）。
version: 0.3.0
metadata:
  category: pipeline
  route: 本地零成本
  proven: 2026-08-24 DEV-MACPRO M2 Max
  upstream: local-sdxl-wallpaper
---

# 本地 Wan2.2 循环壁纸产线

## ★ 核心手法：循环是**约束**，不是**结果**

以前的做法：prompt 里写「待机循环」→ 出片 → 测首尾帧 RGB 距 → 不达标返工。**这是碰运气 + 事后补救。**

正解：**把同一张图同时喂给 `WanFunInpaintToVideo` 的 `start_image` 和 `end_image`。**
首尾被钉死成同一帧，循环从「祈祷它能对上」变成「模型必须解出来的边界条件」。

```python
"7": {"class_type": "WanFunInpaintToVideo",
      "inputs": {"positive": [...], "negative": [...], "vae": [...],
                 "width": 512, "height": 768, "length": 33, "batch_size": 1,
                 "start_image": ["4", 0],      # ← 同一个 LoadImage
                 "end_image":   ["4", 0]}},    # ← 同一个 LoadImage
```

模型：`wan22_fun_5B_inp.safetensors`（**必须是 InP 版**，普通 Wan2.2 没有首尾帧输入）
CLIP：`umt5_xxl_fp8_e4m3fn_scaled.safetensors`（type=`wan`）· VAE：`wan2.2_vae.safetensors`
采样：**20 步 · CFG 5.0 · uni_pc / simple**

---

## ★ 步数：不要用 8 步（实测证伪）

Turbo/Lightning LoRA 是按 **4 步**蒸馏的。跑 8 步会破坏它的去噪调度表，出来更糊不是更好。

**要么 4 步（带 Turbo LoRA），要么 20 步（不带）。8 步是两边不讨好。**
本产线走 20 步 —— 用户口径是「按质量/精度/精美/爆款需求走，不按速度」。

---

## ★ 交付格式：`SaveAnimatedWEBP` 出的片用户打不开

它编的是 **VP9**，QuickTime、微信、剪映、大部分播放器都不认。用户原话：「你视频产物是空的 打不开」。

**出片一律同时转两份：**

```bash
# H.264 MP4（通用播放）
ffmpeg -y -i in.webp -movflags +faststart -pix_fmt yuv420p \
       -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -c:v libx264 -crf 18 out.mp4

# GIF（聊天窗口直接预览，用户第一眼就能看）
ffmpeg -y -i in.webp -vf "fps=12,scale=360:-1:flags=lanczos,split[a][b];\
       [a]palettegen[p];[b][p]paletteuse" out.gif
```

**归档三件一起：`.webp`（源）+ `.mp4`（播放）+ `.gif`（预览）。**

---

## ★ 待机 prompt：只写微动，把「不许动」写进正向

```
正向  She stays in place and breathes gently. Her chest rises and falls slowly,
      strands of hair and the hem of her clothes drift in a faint breeze,
      she blinks once, her gaze stays on the viewer.
      The camera does not move. The background does not change.

负向  camera movement, zoom, pan, cut, scene change, extra person,
      morphing face, distorted hands, flicker, watermark, text
```

要点：
- **别写姿势和服装** —— 首帧已经钉死了，再写只会让模型试图改它 → 变形
- 「相机不动 / 背景不变」写**正向陈述句**（Wan 是 T5 语义编码，吃自然语言，跟 SDXL 的 tag 逻辑相反）
- 眨眼只写 `blinks once` —— 33 帧 @16fps ≈ 2 秒，眨两次会显得抽搐

---

## ★★ 卡死的真凶是**进程寿命**，不是分辨率（归因反复过一次）

**先写结论：Wan 出片前先重启 ComfyUI。**

2026-08-24 实测时间线：
1. 704×1280 · 33帧 → 采样 22分28秒，**VAE 解码 20 分钟无产出**，中断
2. 我据此写下「704×1280 本机不可行」→ **错的**
3. 512×928 → 采样只要 7分40秒，**解码照样卡死**
4. 换 `VAEDecodeTiled`（temporal_size 8）→ **还是卡死**
5. **完整重启 ComfyUI** → 空闲内存从 73MB 回到 **22.8GB** →
   **同一个 512×928 配置一次跑通**

> 进程跑了 5.5 小时、反复加载 SDXL / Wan / UMT5 三套模型，
> 累积占用 **22.8GB**。VAE 解码要一次性分配 33 帧的输出与中间张量，
> 剩下那 73MB 不够，于是死在换页上 —— **表现像「太慢」，其实是「没内存」。**

### 判据：怎么区分「在算」和「卡死」
```bash
P=$(lsof -nP -iTCP:8188 -sTCP:LISTEN -t | head -1)
ps -o time= -p $P; sleep 20; ps -o time= -p $P   # CPU 时间几乎不涨 = 不是在算
vm_stat | sed -n '2p'                             # Pages free 掉到万位以下 = 内存见底
sysctl vm.swapusage                               # swap 用尽 = 已在换页
```

### 实测耗时（重启后的干净进程）
| 配置 | 采样 | 结论 |
|---|---|---|
| **512×928 · 33帧** | **7分40秒** | ✅ 生产基线，出片 2.2MB |
| 704×1280 · 33帧 | 22分28秒 | 🟡 采样确实慢 3 倍（真实分辨率成本），但**不是不可行** |

**生产建议**：512×928 出片（比例 1.8125 ≈ 704×1280 的 1.818），
再用 `出片转码.py --scale 704:1280` 放大回规格档。省 15 分钟，肉眼无差。

---

## ★★ 交付格式：本机 ffmpeg 解不了动画 WebP

`SaveAnimatedWEBP` 的产物直接喂 ffmpeg 会报
`invalid TIFF header in EXIF data` / `image data not found`，
**产出 0 字节的 mp4/gif 而退出码仍是 0**（ffmpeg 8.1.2-tessus 实测）。

**正解：PIL 拆帧 → ffmpeg 拼装。** 已封进 `02_通用资产/出片转码.py`：
```bash
python3 出片转码.py 片.webp --outdir 目录 --scale 704:1280 --gif-width 340
```
它会拆帧、转 H.264 MP4 + GIF，并**逐个 ffprobe 验有没有视频流**才算通过。

> 这条正是为什么判据要定成「ffprobe 读到视频流」而不是「退出码 0」——
> 退出码 0 的那两个文件是空的。

---

## ★ 验收判据

1. **能不能播** —— 先 `ffprobe` 看 MP4 有没有视频流，再自己打开看，别把「转码命令退出码 0」当通过
2. **首尾接得上** —— 首尾帧同图法理论上天然对上，但仍要肉眼过一遍循环点
3. **人物没变形** —— 脸/手在中间帧最容易崩，逐帧抽查而不是只看首帧
4. **产物不是空的** —— 落盘文件大小合理（512×768×33 帧的 webp 通常 ≥300KB）

**成败都要发给用户看。** 用户原话：「无论成功与否 无论视频阶段还是照片阶段 你都要给我看产物」。

---

## ★ 上游给我什么：R02-001 锚图规格

下游需求写在 `05_对标博主蒸馏/_取用/02_类目输入清单.csv`，**开工前先读**：

> **R02-001 锚图（动效用）· 必需 · 704×1280（生产档）/ 512×512（验收档）
> · 单人居中 · 留边 ≥8% 避免裁切 · 1张/条 · 同角色 ≥2 变体**

**留边 ≥8% 是给动效留的余量** —— 人物贴边的图，一动就会被裁掉肢体。
上游 `local-sdxl-wallpaper` 出图时靠 `(full body, feet visible, head to toe:1.2)`
加负向 `cropped, out of frame, cut off` 保证。

其它相关规则：
- `RULE-CAT02-001`：**功能型标题**（带 #动态壁纸 / #锁屏 这类用途词）
  中位赞 **59500** vs 品类词 **428** —— **139 倍差距**，标题词性比画面还关键
- `RULE-CAT02-002`（≤5s 待机循环 × 首尾无缝 × 前3秒AI标识）标着
  **「★观察期·推导非实证」** —— ② 主对标博主 = 0 人，**这条规则本身还没有实证支撑**，
  别当实证结论用。**AI 标识漏标累计 3 次限流 30 天。**

---

## ★ 与静态线的接法

```
local-sdxl-wallpaper 出图
   → 人工验收（裆部无性暴露 + 手正常 + 标志特征在）
   → 拷进 ComfyUI/input/
   → 本 skill 首尾帧同图
   → 转 MP4 + GIF
   → 归档 04_素材产线/输出/循环壁纸-YYMMDD/
```

**只拿已验收的静态图当首帧。** 拿废图当首帧只会把废图变成会动的废图。

---

## ★ 共享环境纪律

ComfyUI（`localhost:8188`）是**多线程共享**的（Kimi Code 也有一个 2D 线程在用）。

- ✅ **正常排队**，FIFO 会轮到你
- ❌ **不许 `POST /queue {"clear": true}`** —— 会清掉别人的任务（我犯过）
- 排队前先 `curl -s localhost:8188/queue` 看清楚别人在跑什么，报给自己的日志，不干预
