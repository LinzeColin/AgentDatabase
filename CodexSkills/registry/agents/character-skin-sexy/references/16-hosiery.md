# 丝袜类型：不是一律黑丝（sexy 版）

**和 pipeline 的差异只有两条**，其余（三层优先级、九种类型、市场回填）完全一致：

1. **丝袜是必选项**，不是可选项——sexy 的三维度里 ③「丝袜/性感/肉感」是必须满足的，
   所以 `canonical` 只在 `r5` 幼态豁免时出现，其它情况必须落到具体丝袜类型。
2. **允许更强的类型**：`fishnet`（渔网）、`patterned`（花纹）在 sexy 里可选，
   pipeline 里一般不用——公开平台上这两类更容易被判定为软色情。

**`r5` 幼态体型豁免在 sexy 里同样不可协商**：照原设，不加任何丝袜条款。
这条不因为 skill 不同而放宽。

---


**用户 2026-08-23 指出的问题**：产线一直只写 `sheer stockings`，模型默认给黑丝。
但有的角色适合白丝、有的适合长筒袜/连裤袜/厚黑丝，**要按热度和市场接受度选**。

配置在 `research/hosiery.json`，`build_taskpack.py` 按角色取用。

## 九种类型

| key | 中文 | prompt 措辞 |
|---|---|---|
| `black_sheer` | 黑丝（薄） | `sheer black stockings with a visible lace top band` |
| `black_opaque` | 厚黑丝 | `opaque black tights, matte finish` |
| `white_opaque` | 白丝 | `opaque white thighhighs with a clean top band` |
| `white_sheer` | 白丝（薄） | `sheer white stockings` |
| `pantyhose` | 连裤袜 | `full-length sheer pantyhose covering hip to toe` |
| `over_knee` | 长筒袜 | `ribbed over-the-knee socks reaching mid-thigh` |
| `patterned` | 花纹袜 | `patterned stockings echoing the outfit's own motif` |
| `fishnet` | 渔网袜 | `fine fishnet stockings` |
| `canonical` | 照原设 | `legwear exactly as in the reference image` |

## 怎么选：三层，优先级从上到下

### 第一层 · 硬约束（不可协商）

- **`r5` 幼态体型角色 → `canonical`**，照原设，不加任何丝袜条款

### 第二层 · 逐角色覆写（用户说了算）

`hosiery.json` 的 `overrides` 里写 `"<game>/<character>": "<type>"`，直接生效。
**这一层是给用户用的**——他知道哪个角色适合什么，比任何规则准。

### 第三层 · 按原设配色自动推断（兜底）

| 原设主色 | 选 | 为什么 |
|---|---|---|
| 白/浅/粉/圣洁系 | `white_opaque` | 同色系顺色，最常见的高接受度组合 |
| 黑/深紫/哥特/暗色 | `black_sheer` | 同色系顺色 |
| 红/橙/暖色 | `black_sheer` | 暖色配黑丝是高对比，市场最熟悉的搭法 |
| 学院/制服/运动风 | `over_knee` | 品类内自然，不违和 |
| 和风/华服 | `white_opaque` | 和风白足袜的延伸 |
| 原设腿部服装本身就好看 | `canonical` | 改了反而偏离基准特征 |

**主色从锚图算，不靠我判**：取人物区下三分之一（腿部与裙摆）的主导色相。

## 让选择从"推断"变成"实测"

`hosiery.json` 有一段 `market.records`，发布后回填：

```json
{"id":"genshin/yelan/default","type":"black_sheer",
 "曝光":12400,"完播":0.31,"点赞率":0.042,"限流":false}
```

**攒够 20 条以上样本，就让实测排序取代第三层的推断规则。**
在那之前第三层只是兜底，不是结论——我没有市场数据，
上面那张表是按配色协调推的，**不是按热度实测的**，这一点必须说清楚。

## 和「不偏离基准人物特征」的关系

pipeline 严格禁止偏离基准特征，但**基准特征指的是脸、发色发型、瞳色、标志配饰、配色**，
腿部服装不在其中——所以换丝袜类型不算偏离。
但若角色原设的腿部服装本身就是标志性配饰（例如带纹样的护腿），那就走 `canonical`。
