# 手：这条产线最高频的缺陷，单独立一章

**实测：用户挑出的 13 张缺陷图里，10 张是手的问题。** 其余的解剖问题加起来不到它的三分之一。

## 手的缺陷分五类，判据各不相同

| 类 | 表现 | 判据（人看一眼能判的） |
|---|---|---|
| **多手** | 三只手／凭空多一只 | 数手掌。超过 2 就是坏 |
| **重影** | 同一只手叠了两层轮廓、六七根手指 | 手指边缘有半透明副本 |
| **穿模** | 手臂／手穿进胸部、腰、道具里 | 肢体与躯干交界处没有遮挡关系 |
| **模糊** | 单只手糊成一团，其它部位清晰 | 同图对比：脸清楚、手不清楚 |
| **朝向反** | 手心手背朝向与手臂扭转不符 | 顺着前臂看拇指该在哪一侧 |

## prompt 里必须写死的手部条款

`regen.py` 的 `FIX` 与任务包 prompt 都要带这一段。**逐条对应上面五类**，
不是笼统写「correct anatomy」——那句话在 594 条 prompt 里出现过，照样出三只手。

```
HANDS (the single most failure-prone part of this image):
Exactly two hands total, no more. Each hand traces cleanly from fingertips to palm
to wrist to forearm to upper arm to a visible shoulder joint on the correct side of
the torso. Five fingers per hand with one clearly separate thumb; no sixth finger,
no fused or duplicated fingers, no ghosted or doubled hand outline.
Palm-versus-back orientation must follow the forearm's rotation the way a real hand
does: the thumb sits on the radial side, and a visible palm means the forearm is
supinated.
Hands never intersect the chest, torso, hair or any prop — where a hand overlaps
something, render a clear occlusion edge, not a blend.
Both hands are rendered at the same focus and detail level as the face; a blurred
or smudged hand is a defect even if everything else is sharp.
```

## 关键限制：**这条产线做不到「只修手」**

`gpt-image-2` 的 `images/edits` 是**整图重绘**，不是局部重绘。
用户说「仅修改手部，其余全部都不要动」——**技术上做不到**，必须提前讲清楚：

- 能做的：拿同一张锚图 + 同一段 prompt + 手部条款重出，构图/服装/场景**高度相似**
- 做不到的：像素级保留其余部分

**每次重出前都要说这一句**，不然交付时用户会发现「别的地方也变了」，
那是把发现成本转嫁给他。

真要局部重绘，得换有 inpainting + mask 的通路（本地 ComfyUI），
而那条路的画质本项目已经证否过。

## 重出策略

1. **保留原图**：改名 `<side>.rejected-N.png`，新旧都留，让用户挑
2. **带上具体缺陷描述**：`--note "上一版右手和胸部穿模"`，
   泛泛的「手有问题」不如一句具体的
3. **手部缺陷不降色情度档位**：手坏和被安全系统拦是两回事，
   降档解决不了手，只会白白降低色情度
