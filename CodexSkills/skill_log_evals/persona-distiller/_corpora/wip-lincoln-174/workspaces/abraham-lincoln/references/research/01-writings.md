# Writings and systematic works

## Scope and assigned sources

**本道分到 44 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-2723a0056843` | 1862 | P1 | Insurgent privateers in foreign ports : message from the P…t privateers in foreign ports |
| `src-9e17d9796521` | 1865 | P1 | Gems from Abraham Lincoln : born February 11th, 1809, in H…5th, 1865, at Washington, D.C |
| `src-c80788c2eea1` | 1902 | P1 | Complete works : |
| `src-bdc84412b7df` | 1903 | P1 | Complete works of Abraham Lincoln |
| `src-05936dd1587b` | 1905 | P1 | The writings of Abraham Lincoln; |
| `src-0ac5bc9653c1` | 1905 | P1 | Complete works of Abraham Lincoln |
| `src-0cbd54408b14` | 1905 | P1 | Complete works of Abraham Lincoln |
| `src-0d2525d49e61` | 1905 | P1 | Complete works of Abraham Lincoln |
| `src-2709403b5402` | 1905 | P1 | Complete works of Abraham Lincoln |
| `src-3ece5a115755` | 1905 | P1 | Complete works of Abraham Lincoln |
| `src-40dea3180bd4` | 1905 | P1 | Complete works of Abraham Lincoln |
| `src-420cfacc1b7a` | 1905 | P1 | Complete works of Abraham Lincoln |
| `src-4f1fe162a884` | 1905 | P1 | Complete works of Abraham Lincoln |
| `src-533cd619bcd0` | 1905 | P1 | Complete works of Abraham Lincoln |
| `src-56d370d40945` | 1905 | P1 | Complete works of Abraham Lincoln |
| `src-5d7e14cf08e2` | 1905 | P1 | Complete works of Abraham Lincoln |
| `src-5ef6cad0be44` | 1905 | P1 | Complete Project Gutenberg Abraham Lincoln Writings |
| `src-6ba0625bdf71` | 1905 | P1 | The writings of Abraham Lincoln |
| `src-732a649f26ff` | 1905 | P1 | Complete works of Abraham Lincoln |
| `src-73daf6c97460` | 1905 | P1 | Complete works of Abraham Lincoln |
| `src-77eca3ffa74f` | 1905 | P1 | The writings of Abraham Lincoln |
| `src-78d403e6d5f5` | 1905 | P1 | Complete works of Abraham Lincoln |
| `src-93c32e416ad7` | 1905 | P1 | Complete works of Abraham Lincoln |
| `src-9a3f427492d9` | 1905 | P1 | Complete works of Abraham Lincoln |
| `src-a50adfc3d4fb` | 1905 | P1 | Complete works of Abraham Lincoln |
| `src-accfb35ec5a5` | 1905 | P1 | The writings of Abraham Lincoln |
| `src-b4caa81ea573` | 1905 | P1 | Complete works of Abraham Lincoln |
| `src-cdb68ea774e5` | 1905 | P1 | Complete works of Abraham Lincoln |
| `src-eda7d8153527` | 1905 | P1 | The writings of Abraham Lincoln; |
| `src-f9611096ce5f` | 1905 | P1 | Complete works of Abraham Lincoln |
| `src-fe2a0f60853f` | 1905 | P1 | Complete works of Abraham Lincoln |
| `src-17e372b665cb` | 1906 | P1 | Complete works of Abraham Lincoln |
| `src-5c96f622593c` | 1906 | P1 | Complete works of Abraham Lincoln |
| `src-6d5409e5b358` | 1906 | P1 | Complete works of Abraham Lincoln |
| `src-7562ecd0b70d` | 1906 | P1 | The writings of Abraham Lincoln; |
| `src-7a4265076f1c` | 1906 | P1 | The writings of Abraham Lincoln |
| `src-85a1bad742d4` | 1906 | P1 | The writings of Abraham Lincoln |
| `src-e343dec9cc6b` | 1906 | P1 | Complete works of Abraham Lincoln |
| `src-ec23f282b09c` | 1906 | P1 | The writings of Abraham Lincoln; |
| `src-0004a5f8b45d` | 1907 | P1 | Life and works; |
| `src-a6dbf2130a2f` | 1907 | P1 | Life and works of Abraham Lincoln |
| `src-c45f37859100` | 1907 | P1 | Life and works of Abraham Lincoln |
| `src-d2370d713009` | 1907 | P1 | Life and works; |
| `src-9cfd53e7a422` | 1923 | P1 | The writings of Abraham Lincoln, The Lincoln-Douglas Debates-I |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

**口径**：以下每条都带 `source_id` 与 `norm_offset`；定位可复算——

    text = re.sub(r"\s+", " ", dehyphenate(open(local_path).read()))
    assert text[norm_offset:norm_offset+len(quote)] == quote

三条已现场复算通过。**逐条经人判说话人**，工作稿见 `01-writings.md.observations`。

### O-1 · 他把「离开」讲成失去依靠，而不是讲成使命

> `My Friends: No one not in my position can appreciate the sadness I feel at this parting.`
> —— `src-9e17d9796521` @4165（1865 年编本）

★ 值得注意的不是伤感本身，而是**他用「没有人处在我的位置就体会不到」来立论**：
把个人处境当作论据的起点，而不是把使命当起点。

### O-2 · 他引自己的旧话来自我设限，而不是来立威

> `I do but quote from one of those speeches when I declare that "I have no purpose,
>  directly or indirectly, to interfere with the institution of slavery in the States
>  where it exists.`
> —— `src-c80788c2eea1` @1492（1902 年编本；文本为第一次就职演说）

★ 句式是 **`I do but quote from…`**——他先声明自己只是在复述旧话，
再给出一条**限制自己权力**的承诺。这是一种把新表态锚在旧记录上的做法。

### O-3 · 断言用「我相信」起头，且断的是**制度能不能持续**，不是谁对谁错

> `I believe this Government cannot endure permanently half slave and half free.`
> —— `src-e343dec9cc6b` @11506（1906 年编本；文本为 1858 年 House Divided 讲词）

★ 主语是 `this Government`、谓语是 `endure`——**问的是可持续性**，
不是道德归责。与 O-2 的自我设限放在一起看，是同一种「先缩小自己主张的射程」的手法。

---

## ★ 本节没有写、且**不能靠这批语料写**的

- **两条待定**（一条以「I do not hold the South responsible」起头、一条讲铁路法案与 Zadoc Casey）
  定不到具体讲词与日期，**不进断言层**（[[self-report-is-not-evidence]]）。
- **四条已剔除**，其中一条五道机械判据全过而仍不是他说的：
  以「In 1848, when I first went on the bench」起头那句 —— **林肯没当过法官**。

★★ **这三处有意不加反引号。** `check_lane_quotes_verbatim.py` 会把
  研究稿里**反引号包起来的片段一律当成引文提走**——它只验逐字，不问归属。
  先前这三处带反引号时，判据从本文件提出 **6 条**引文并全部「核过」，
  于是**三条我明确判为「不是他说的」的句子，在判据眼里与另外三条无差别**。
  ⇒ 反例要能读到，但**不能长成引文的样子**。
- `writings` 道 44 条里，**前置页不含第三方编者/导言/悼词的只有 9 条**
  （`front_matter_third_party`）。**观察层的可取面是 9 条，不是 44 条。**
## Candidate Claims

Pending.

## Contradictions and alternative explanations

Pending.

## Unknowns and source gaps

Pending.

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

Pending.
