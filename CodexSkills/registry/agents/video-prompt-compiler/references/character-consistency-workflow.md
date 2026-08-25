# 人物与产品连续性工作流

## 默认链路

```text
Reference Sheet / Identity Sheet
→ approved scene anchor frame
→ one locked reference source reused across shots
→ per-shot motion prompt
→ continuity review
```

## Reference Sheet 至少包含

- 正面、左右 3/4、侧面；
- 中性表情和少量关键表情；
- 发型、服装、配件、比例；
- 产品则改为正面、侧面、背面、关键结构、材料和文字；
- 统一光线与无歧义背景。

## 每镜头重锚

每个镜头重复最小身份锚点，而不是重新创作完整外观：脸/轮廓、发型、服装、关键配件、产品几何、色彩和禁止变化。

## 多参考冲突

不同图片的脸、服装、比例或光线冲突时，减少参考并指定主参考。不要试图用更长 Prompt 调和不一致素材。

## 证据级别

“锁定同一参考节点比每镜重新 Prompt 更稳定”来自 2026 年 Reddit 社区案例，只作为低置信度实践线索。正式结论必须通过目标模型、多场景、多镜头盲测。
