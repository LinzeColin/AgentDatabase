# External accounts

## Scope and assigned sources

**本道分到 4 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-4603171fd82d` | 1908 | S1 | Report of the proceedings of the International Free Trade Congress, London, August, 1908 |
| `src-c9bbe07b2555` | 1915 | S1 | Great speeches of the war |
| `src-85285ec0b5d9` | 1919 | S1 | 1914 |
| `src-6e3057d83176` | 1923 | S1 | Mark Sykes : his life and letters |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

### O-1 · 同时代记录里，他被当作「政府代表」而不是演说家

`src-4603171fd82d`（1908，《Report of the proceedings of the International Free Trade Congress, London, August, 1908》）：

> `is in such cordial union with us upon this great question, to address you. The Right Hon. Winston S. Churchill (President of the Board of Trade) said : I am ve`

1908 年那场自由贸易大会的会议记录把他写成 **the President of the Board of Trade, and the representative of His Majesty's Government**。
判据：**别人记录他时给的是职务**，而他自己写东西时几乎不提职务。

### O-2 · 同一场会上有人当面说他的部门与他本人不一致

`src-4603171fd82d`（1908，《Report of the proceedings of the International Free Trade Congress, London, August, 1908》）：

> `various manufacturing interests, waited on the Minister. “ The farming industry, while expressing grave disappointment at no reduction in the tariff, yet made no`

会议记录里有人说：他的部门在推进保护主义的论证，**而他本人是个彻底的自由贸易者**。
判据：这是**第三方留下的、与他自述不一致的一条**——external 道的价值正在于此。

