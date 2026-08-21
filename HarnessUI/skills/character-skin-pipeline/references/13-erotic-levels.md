# 色情度档位 L1–L5：出图率与色情度的取舍

**结论先行：不要挑一档跑全量，要用阶梯降级重试。**
第 1 次 L4、第 2 次 L3、第 3 次 L2；L2 还出不来就标记为需重做。
实现在 `tools/erotic_levels.py`，`batch_run.py` 按 `attempt` 自动降档。

---

## 五档各自包含什么

| 档 | 相对上一档砍掉 | 这一档还留着 |
|---|---|---|
| **L5** | —（全强度） | 吊袜带 · **露腰** · **深V** · **高衩剪影** · **含胸挺腰** · **暗示性姿态** |
| **L4** | 暗示性姿态 | 吊袜带 · 露腰 · 深V · 高衩 · 含胸挺腰 |
| **L3** | 含胸/挺腰 | 吊袜带 · 露腰 · 深V · 高衩 |
| **L2** | 露腰 / 深V / 高衩 | 吊袜带 · 露肩露臂露腿 · 胸线强调 · pin-up 取向 |
| **L1** | 吊袜带 · pin-up 取向措辞 | 丝袜 · 露肩露臂露腿露胸线（= v1.7.0 原版） |

### 逐档的确切措辞

**L5 的完整条款**（任务包里存的就是这一档，降级在运行时做）：

```
MANDATORY WARDROBE AND PRESENTATION — applies to every character without exception,
this is glamour pin-up art and the wardrobe rule is not optional: sheer stockings,
tights or thighhighs on fully visible legs, worn with visible garter straps. Where the
canonical design has trousers, greaves or armoured legs, restyle the legwear into sheer
stockings or thighhighs while keeping that design's own colours, patterns and trim.
The silhouette is maximally skin-revealing: bare shoulders, bare arms, bare midriff,
fully bare thighs above the stocking band, and a deep plunging neckline. Favour
high-cut leotard, micro-skirt, bodysuit and open-side silhouettes over anything that
covers the hips or waist.
PIN-UP DIRECTION: emphasise the unbroken leg line from hip to ankle and the bust line;
the pose is consciously alluring and suggestive — weight on one hip, arched back,
chin slightly lowered, direct eye contact with the viewer.
```

| 降到 | 替换 |
|---|---|
| **L4** | `consciously alluring and suggestive` → `elegant and poised` |
| **L3** | 再删 `arched back, chin slightly lowered,` |
| **L2** | 整段 `maximally skin-revealing … covers the hips or waist.` → `open and skin-revealing — bare shoulders, arms, thighs and décolletage.` |
| **L1** | 再删 `, worn with visible garter straps`、`PIN-UP DIRECTION: …bust line; `，标题回到 `MANDATORY WARDROBE — applies to every character without exception:` |

---

## 实测数据（这是选档的唯一依据）

### 大样本（全量跑出来的）

| 档 | 样本 | 通过 | 通过率 |
|---|---|---|---|
| **L5** | 110 张（重试 3 次） | 43 | **39%** |
| **L1** | 94 张（v1.7.0 全量） | 94 | **100%** |

L5 那一轮里，昼夜**成对**可用的只剩 **9 / 55 个变体**，单张成本从 $0.07 涨到 $0.34。

### 五档 × 三样本的阶梯（n=3，噪声大）

| 档 | chiz | aurelia | shinku |
|---|---|---|---|
| L5 | 拦 | 拦 | **过** |
| L4 | 拦 | **过** | 拦 |
| L3 | 拦 | 拦 | **过** |
| L2 | **过** | **过** | 拦 |
| L1 | **过** | **过** | **过** |

---

## 最关键的一条：**安全系统有随机性，不是固定阈值**

上表**不单调**：shinku 在 L5 和 L3 过，却在 L4 和 L2 被拦；aurelia 正好相反。
同一档同一张，重试也会得到不同结果（普罗米娅那两张第一次被拦、重试通过）。

**推论一**：`n=3` 的阶梯定不出档位，拿它下结论就是骗人。
**推论二**：「挑一档跑全量」是错的做法——档位高的那些图里，本来有一部分是能过的。
**推论三**：正确做法是**降级重试**，既拿到能拿到的最高色情度，又不整张丢掉。

同时强度确实有影响（L5 39% vs L1 100%），所以要**同时**利用两者：降档 + 重试。

---

## 定档规则

- **起点 L4**，依次降 L3、L2
- **L2 是最低可接受档**。连 L2 都出不来的，标记为需重做，不许自动降到 L1 交差
- **L1 不进重试阶梯**，只作兜底参考

## 成本影响

| 策略 | 92 张的预期 |
|---|---|
| 只用 L5 | 约 39% 成，$6 换 36 张 |
| L4→L3→L2 阶梯 | 预计 85%+ 成，$7 换 78 张以上 |
| 只用 L1 | 100% 成，但色情度回到上一轮水平 |

## 有一类角色不适用

花名册里明显儿童体型的（可莉、七七、菲林一类），这套档位不适用，保持原设服装。
不是可配置项。
