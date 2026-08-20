# 锚图：角色还原度 100% 来自它，不来自 prompt

## 三条选取规则，按优先级

### 1. provenance 优于分辨率

**先按文件名筛出立绘类，再在其中比大小。** 直接按像素面积挑会挑到抽卡横幅——
164 个角色里错了 51 个，包括甘雨（她的横幅比自己的立绘还大）。

各游戏的候选名（探测出来的，别照搬）：
```python
"genshin": ["{n} Card.png", "Character {n} Full Wish.png",
            "Character {n} Full Wish Alt.png", "Character {n} Portrait.png"],
"hsr":     ["Character {n} Splash Art.png", "Character {n} Card.png",
            "{n} Card.png", "Character {n} Portrait.png", "Character {n} Full.png"],
"zzz":     ["Agent {n} Full.png", "Mindscape {n} Partial.png",
            "Agent {n} Portrait.png", "{n} Card.png", "Agent {n} Splash Art.png"],
"wuwa":    ["{n} Full Sprite.png", "{n} Splash Art.png", "{n} Card.png"],
```
**`"{n} Wish.png"` 是抽卡横幅（2048×1024，宽），必须排除。**

探测新游戏的命名：拿一两个角色页 `prop=images&imlimit=200`，
筛含 `Full/Splash/Portrait/Card/Artwork/Render/Sprite` 的 png，看规律。

### 2. 竖构图优于面积

```python
max(found.items(), key=lambda kv: (1 if kv[1][1] >= kv[1][0] else 0, kv[1][0]*kv[1][1]))
```
横幅像素再多，人物也是被裁过的。

### 3. 必须 `?format=original`

Fandom 的 CDN 对**所有** user-agent 返回有损 WebP 转码。同一个 750×1800 文件：
转码 313KB vs 原图 1.66MB。

```python
parts = urlsplit(url); q = parse_qs(parts.query); q["format"] = ["original"]
url = urlunsplit(parts._replace(query=urlencode(q, doseq=True)))
```

## 换装的锚图：page image 不一定是人物像

`collect_outfits.py` 原来拿 outfit 页的 `pageimages` 当锚图。**在鸣潮上那是错的**：
它的 page image 是 `<Outfit> Splash Art.png` —— 整套场景的宣传图，
2048×1667 全是房间，人物小小地躺在中间某处。当身份锚图等于没有锚。

正确的是 `<Outfit> Full Sprite.png`（竖构图的人物立绘）。
**先按名字要 sprite，wiki 没有才退回 page image**——而没有 sprite 的那几套，
宁可不收：

```python
sprite = sprites.get(title)          # File:<Outfit> Full Sprite.png
if not sprite:
    orphans.append(f"{title} (只有场景宣传图，没有 Full Sprite)")
    continue
```

鸣潮 5 套「真·另一套」里只有 2 套有 Full Sprite。拿场景图跑过一次试跑：
图本身能看，**但同一套换装的昼版和夜版长得不是一套衣服**——
锚图弱到锁不住身份。而昼夜是同一张皮肤的两面，不一致就是缺陷。

> 附带一次静态误判：这两张场景图锚图第一次提交被 safety system 拒了，
> 我据此以为是内容被封。第二轮重试**同样的请求通过了**——是瞬时抖动，不是必然。
> **一次拒绝不构成结论**，重试一次再下判断。

顺带：`collect_outfits.py` 下载时也要 `?format=original`，
否则拿到的是 CDN 的 WebP 转码（同一个 1200×1600 的文件会被喂成 2048×2048 的转码版）。

## 存法

落盘前 `thumbnail((2048, 2048))` 统一上限，存 JPEG q95。
同目录写 `source.json` 记 `wiki_title` / `url` / 原生尺寸——
后面要核「这张图哪来的」时不用重新猜。

## 验收锚图质量

抓完看两个数：
- **构图分布**：竖 / 横。全竖才正常（鸣潮 41/41 竖）
- **短边中位数**：< 1000px 说明这个游戏的 wiki 素材不行，要换源
  （原神/崩铁/绝区零/鸣潮实测中位 1748px）
