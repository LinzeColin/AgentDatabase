# 接手这个仓 —— 从这里开始

> **给委托人的一句话 prompt**（复制粘贴给任何一个 AI 助手，不限厂商）：
>
> ```
> 读这个仓根目录的 START-HERE.md，按它说的接着做，不要问我怎么设置。
> ```
>
> 就这一句。**不需要装任何东西，不需要配置任何东西。**

---

## 一、这个仓是干什么的

把**已故的、作品在公有领域的**人物，从一手原始语料蒸馏成可被 AI 调用的「人物档案」，
并用**盲判**证明这份档案确实让模型答得更好（而不是只是文风变了）。

**核心约束只有一条：零编造。** 来源、事实、引文、分数，一个字都不许编。
所有数字都必须是**跑出来的**，不是写出来的。

## 二、现在做到哪了（★ 这张表由判据现算并写入，不许手改）

| | |
|---|---:|
| 已入库人物档案 | **102** |
| 在制工作区 | **53** |
| 语料（★ 两处布局，口径见下） | **6,494 份** ＝ `raw/` 3,780 ＋ `references/sources/` 1,999 ＋ 其它布局 715 |
| 断言 | **1,011 条** |
| 盲判用例 | **1,046 题**（50 个工作区） |
| 记延后/拒发 | **185 条**（都写明了理由与解锁条件） |

**这六格自己重算一遍**（也是它们唯一的写入口）：

```bash
python3 CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline/check_start_here_numbers.py
```

`rc=0` 表示表与实测一致；不一致时它会逐格印出「实测 / 表里 / 口径」，
`--apply` 整格重写。**它也接在移交包的回读自验证里**，所以这张表不会再悄悄漂。

> ★★ **但这一页上有判据管着的只有这 6 格。** 本页「数字＋量词」的断言有几十处，
> **除这 6 格外没有任何判据管**。要现数就跑（数会随每次编辑变，所以**这里不写死**）：
>
> ```bash
> python3 - <<'EOF'
> import pathlib, re
> t = pathlib.Path("START-HERE.md").read_text(encoding="utf-8")
> p = re.compile(r"\*\*([\d,]+)\s*(条|个|份|人|行|题|KB|道)\*\*|(?<![\d])([\d,]{2,})\s*(条|个|份|人|行|题|KB|道)")
> print(sum(len(p.findall(l)) for l in t.splitlines()), "处数字断言｜其中有判据管的：6")
> EOF
> ```
>
> > ★★★ **这一段自己就踩了一次**：我先写死「共 49 处」，
> > 而**加上这一段之后立刻变成 55 处** —— 一句关于「数字会漂」的话，
> > 在写下的同一秒就把自己写漂了。所以改成给命令，不给数。
>
> 那些没人管的断言里，有一部分是**有意的历史陈述**（「8-13 白天写的是 24／14／10／0」
> ——记的是当时错在哪，不该被「更新」），另一部分是现状。
>
> 当天按「假装我是接手的人」逐条读过一遍，**改掉了 7 处漂掉的现状数**：
> `.py` 669→**682**、踩坑库 165→**193**、HANDOFF 120KB→**127KB**、
> START-HERE「一页纸」→**389 行**、`emit_ids_rebuild` 19／26→**18／36**、
> 就绪度「5 个人」→**6 人**、「11 人全部就绪」→**17 人**。
> 会继续漂的几处已改成**指向真源 ＋ 附现算命令**，而不是把数字再抄一遍。
>
> ⇒ **读到本页任何一个没带现算命令的数，先当它可能是旧的。**
> [[every-requirement-needs-an-owner]]｜[[read-the-artifact-as-its-actual-reader]]

★ **口径一律是 `git ls-files`** ——「你 clone 之后真正拿到的东西」，
不是某台机器的磁盘状态。三处布局必须分开看：

| 放哪 | 份数 | 说明 |
|---|---:|---|
| `references/sources/<src-id>/*.normalized.txt` | 1,999 | 老工作区 |
| `**/raw/*.txt` | 3,780 | 早期提交进去的 |
| 其它布局 | 715 | 更早的扁平目录 |

★ **新工作区的 `raw/*.txt` 已被 `.gitignore` 挡在仓外**，所以不在上表里：
它们靠每个工作区的 `raw/_ids-rebuild.txt` ＋ `_fetch-manifest.json` 的 sha256 重建。
`emit_ids_rebuild.py --scan _corpora --check` 现测 **rc=0**
（**2026-08-14 实测：一致 18／有问题 0／没有 manifest 的老工作区 36**）。

> ★ 这一行原来写「一致 19／…／26」，**两个数都漂了**（真值 18／36）。要现算就跑那条命令。
>
> ★★ 它的分母 **18＋36 ＝ 54**，而 `wip-*/workspaces/*` 数出来是 **53**；
> 另按 `rglob raw/_fetch-manifest.json` 独立数，有 manifest 的是 **19** 而不是 18。
> **两个口径差 1**，方向指向已知的那件事：**9 个工作区的路径套了两层**
> （`workspaces/<slug>/<slug>/`，见 HANDOFF 开头第 ② 条）——
> 判据按 `iter_workspaces` 走，会把外层那个空 `raw/` 也算一个。
> **本轮没有改判据**（动它要先改台账 `local_path`），只把这个差记在这里，
> 免得下一个人拿两个数对不上又查一遍。

★ 这一页早先的版本这里全是错的——「已入库 71」数的是 `registry/codex/` 下的
**技能目录**（根本不是人物），六格里五格陈旧。表头当时也写着「由脚本现算」，
而**并没有任何脚本在算**。判据就是为这件事写的。

**唯一的停点：阶段 5「判分」还没跑。** 见下面第四节。

## 三、跑起来需要什么

**只需要 `python3`（3.9+）和 `git`。**
全部工具实测只用 Python **标准库**，`pip install` 一个都不用。

★ **这句话 2026-08-14 逐个 import 核过**（`ast` 解析 + 按模块 origin 是否落在标准库目录判）：
persona-distiller 两棵下 **682 个 `.py`**（当日**再测**；早先写的 669 是加今天两件工具之前的数），
非标准库的顶层 import **只有 3 个** —— **这个 3 没变**，逐个查清：

| | 处数 | 实况 |
|---|---:|---|
| `msvcrt` | 50 | **Windows 的标准库**，且写成 `try: import msvcrt / except ImportError: msvcrt = None`——非 Windows 上降级，不是依赖 |
| `registry_core` | 3 | 住在**同仓的兄弟技能** `registry/codex/persona-distiller-group/scripts/`；`check_contract_drift.py` 自己文档写明「按设计如此」。**同一个包里，不用装** |
| `pypdf` | 1 | **唯一一个真第三方**，只在 `_corpora/wip-steinhardt-98/ms_contact2.py` 这个**工作区内的一次性脚本**里，**不是流水线工具**——不跑它就不需要它 |

★ 2026-08-14 新加的两件工具（`fetch_kramerius.py`／`slice_letter_volume.py`）
**逐个查过 import，非标准库 0 个**：
`argparse datetime hashlib json pathlib re sys time urllib` ／ `argparse hashlib json pathlib re sys`。
要现算就跑（本机 py3.9 没有 `sys.stdlib_module_names`，要按 origin 判）：

```bash
python3 - <<'EOF'
import ast, pathlib, sys, sysconfig, importlib.util
STD = pathlib.Path(sysconfig.get_paths()["stdlib"]).resolve()
def std(n):
    if n in sys.builtin_module_names: return True
    try: s = importlib.util.find_spec(n)
    except Exception: return False
    o = (s.origin or "") if s else ""
    return o in ("built-in", "frozen") or (bool(o) and STD in pathlib.Path(o).resolve().parents)
R = [pathlib.Path("CodexSkills/skill_log_evals/persona-distiller"),
     pathlib.Path("CodexSkills/registry/codex/persona-distiller")]
ps = sorted({p for r in R for p in r.rglob("*.py")}); loc = {p.stem for p in ps}
tops = {}
for p in ps:
    try: t = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError: continue
    for n in ast.walk(t):
        if isinstance(n, ast.Import):
            for a in n.names: tops.setdefault(a.name.split(".")[0], []).append(p)
        elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
            tops.setdefault(n.module.split(".")[0], []).append(p)
bad = {k: v for k, v in tops.items() if k not in loc and not std(k)}
print(len(ps), "个 .py｜非标准库", len(bad), "个：", {k: len(v) for k, v in bad.items()})
EOF
```

★★ 但**整个包不止 persona-distiller**：`git clone` 会拿到 `CodexSkills` 下别的技能
（graphify 要 networkx／tree-sitter／neo4j，book-to-skill 要 docling／bs4，dws 要 openpyxl…）
与 `OpenAIDatabase`。**那些跑起来是要装东西的**，只是本页说的这条流水线不用。

验证一下（三条命令都应当立刻返回）：

```bash
python3 --version && git --version && echo OK
```

## 三之二、★★ 语料在哪（**第一次跑之前先读这段**）

**语料不全在 git 里**，这是有意的裁定（仓里只放指针，正文另存）。
**2026-08-13 按 `git ls-files` 口径逐个数过 53 个工作区**（＝你 clone 之后真正拿到的）：

| 情形 | 个数 | 语料在哪 |
|---|---:|---|
| 正文就在仓里 | **32** | `…/references/sources/` 或 `…/raw/`（**只放建模侧那一半**，密封集按设计不在里面） |
| 有重建指针 | **19** | `…/raw/_ids-rebuild.txt`（每行一个 Internet Archive identifier；新工作区的 `raw/*.txt` 被 `.gitignore` 挡在仓外） |
| 空工作区（没开工，台账也空） | **2** | — |
| **取不回来** | **0** | 32 + 19 + 2 = 53，没有第四种 |

★ 这张表**现在由判据管着**（`check_start_here_numbers.py` 的第 7 项），
数字漂了它会红。8-13 白天写的是 24／14／10／0 共 48 个——**那时的结构对、数字旧了**。

★★★ **这个「取不回来 0」的射程只到上面这 53 个**，而 `_corpora/` 下一共有 **75 个 `wip-*` 目录**：
差的 22 个是**扁平布局**（账本直接在 `wip-*/` 下，没有 `workspaces/` 这一层），上表的口径够不着它们。
同一件判据的**第 8 项**改按「账本所在目录」数，把两种布局都收进来，8-13 晚实测：

> **58 个有账本的目录 ＝ 全取得到 38 ＋ 部分 0 ＋ 一条都取不到 19 ＋ 空账本 1**；
> 账本共 **3,901 行**，其中 **1,652 行**的正文不在仓里 ——
> 这 1,652 行里 **1,116 行有 `_ids-rebuild.txt`**（跑一次抓源就回来），**536 行没有**。

★ 2026-08-14 复核：**行数 3,901 对得上，目录数对不上** ——
`rglob source-ledger.jsonl` 独立数得 **60** 个（其中空账本 **1** 个，
`wip-benardos-128/…/nikolai-benardos`），而判据第 8 项报 **58**。**差 2**，
方向与上面「判据分母 54 而 `wip-*/workspaces/*` 是 53」同源（**路径套两层**）。
行数一致说明那 2 个目录里没有额外的账本行，**不影响任何结论**；
**这一格以判据为准**（改它会让门红），差记在这里。
现算：`python3 -c "import pathlib;L=list(pathlib.Path('CodexSkills/skill_log_evals/persona-distiller/_corpora').rglob('source-ledger.jsonl'));print(len(L))"`

**唯一的例外，也是全库唯一真丢的一个：`wip-livermore-100`（Livermore #100，已入库）
—— 账本 536 条、正文 0 份、`_ids-rebuild.txt` 也没有。** 它落在上表 53 个之外，所以那个「0」不算错，
但**别把「取不回来 0」读成「什么都没丢」**。要重建它得从台账里的 `locator`/`url` 重抓（判据不替你做这件事）。
「部分 0」这个数同样要紧：**没有任何一个工作区是「取得到一半」的** —— 要么全在，要么整个靠指针。

★★ 同一个射程问题也落在**交付包自验证**上：那几道语料门取账本的写法是
`wip-*/workspaces/**/evidence/source-ledger.jsonl`，于是台账总行数正好分成三份 ——
**这三个数由两件互不相干的判据各自算出来，加起来正好等于第三个数**（3,901）：

| | 行数 | 谁在核 |
|---|---:|---|
| 真核过校验和 | **2,877** | 自验证日志：`✅ 台账 2877 行：缺校验和 0 行` |
| 扁平布局（账本直接在 `wip-*/` 下），在扫描集之外 | **993** | 无 —— 7 个：galen-101、godin、harvey-103、jenner-104、livermore-100、steinhardt-98、vesalius-102 |
| 两份 `_corpus/source-ledger.jsonl` | **31** | 无 —— 取法只认 `evidence/`（Blackstone #169 15 行 ＋ Holmes #170 16 行） |
| **合计** | **3,901** | ＝ 第 8 项算出来的台账总行数 |

指针那道门**自己是诚实的**（印「**18 个工作区**逐条核 sha256……另有 **35** 个未检查」）。
问题不在假绿，在那 993 ＋ 31 行**连「未检查」都算不上 —— 它们不在任何一个分母里**。
自验证里已加一行把差集印出来并标「**未检查，不是通过**」；**那几道门的读法没有动**
（改一处要连着改四处，不是交付前夜该干的事）。要收干净，就把取账本的写法从
「`evidence/` 下那一份」改成「这个工作区下的**每一份**」，改完拿这张表当回归。

★★ 同一天我用一个临时脚本重数，得出 44／19／9 —— **那是错的**：
`_ids-rebuild.txt` **自己也以 `.txt` 结尾**，于是 19 个「只有指针」的工作区被算成了「有正文」。
判据里那句 `"_ids" not in base` 正是防这个的。**临时脚本别重实现判据的度量。**

★ 密封集不在 `references/sources/` 里**是对的**：那一半按设计不许建模侧读到。
  实测 24 个里 23 个**精确吻合**（缺的份数 = 密封件份数），第 24 个（Rosenhain）
  用的是另一套文件命名，我的匹配器对不上——**不是缺文件**，逐份查过漏出 0 份。

### 所以你第一次跑判据会看到这个，**那不是坏了**

在没有放语料的工作区上：

    check_quote_speaker           → rc=4「**未判**，不是通过」（train 语料 0 份）
    gen_claims.py                 → rc=1（逐字引文回不了语料，**故意不写文件**）
    flag_borrowed_voice --self-test → rc=5「**未跑**，不是通过」（自测的 36 个例子全建在真语料上）
    detect_front_matter --self-test → rc=5「**未跑**」（自测要的 3 份语料不在本树）

★★ **还有两件「按设计就返回 1」的**，别当成坏了（2026-08-14 在一个真 clone 里逐条跑过）：

    check_lane_distinct_works.py  → rc=1（空心道：Churchill／Marshall 是已查清、已落纸的
                                    两例，做成硬绿就永远变不绿——它比对基线名单，**多出新的人才是回归**）
    check_scoring_ready.py        → rc=1（见第五节：1 的意思是「有人缺件、矛盾或压线」）

★ 另有两件**只报数、不是门**的（本轮新做，跑起来不需要判读经验）：

```bash
python3 CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline/check_profile_declared.py
python3 CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline/measure_distinct_works.py --self-test
```

前者答「谁没声明档位、谁声明的档与材料对不上」；后者是判重的正确尺子（`--workspace <工作区>`
真跑要几分钟，全库 `--all` 要几十分钟，结果已存在
`_ledgers/_全库独立作品数重量-2026-08-14.md`）。

### ★ 2026-08-14 上午新加的四件，**打包脚本会自动跑前三件**，你也可以单独跑

```bash
P=CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline
python3 $P/check_pd_claim_has_a_year.py            # 硬门 rc=1：断言公有领域却没有出版年
python3 $P/check_lessons_reach_the_bundle.py       # 报告：写在 ~/.claude/ 里、进不了包的教训
python3 $P/check_namesake_epithet_in_title.py      # 报告：题名里的 il giovane／der Jüngere
python3 $P/check_inflected_byline_candidates.py <工作区> --alias <他在别的语言里的姓>
```

| | 它答什么 | 你会看到 |
|---|---|---|
| `check_pd_claim_has_a_year` | 有没有源在**没有出版年**的情况下断言 `pre1931` | 现在 **0 行**（分母：断言 PD 的 1,379 行）。**红了 `make_handover_bundle.sh` 直接不打包** |
| `check_lessons_reach_the_bundle` | 教训有没有漏在包外 | 在**别人的机器上**会印「**未量，不是通过**」——`~/.claude/…` 那个目录只在原作者机上 |
| `check_namesake_epithet_in_title` | 编目用称谓区分了同名的两个人吗 | 6 行全在 Michelangelo；「仍挂在他名下的**后辈** 0 行」 |
| `check_inflected_byline_candidates` | 「查无署名证据」里，哪些其实扉页上有名字（拉丁属格 `COMENII`、捷克 `KOMENSKÉHO`） | **只交候选**、rc 恒 0。Comenius 22/48、Rousseau 39/45、Bismarck 26/39 |

★★ **最后一件的结果现在不许回填台账** —— rousseau／bismarck／pestalozzi 是
第 1 批**预登记等着判分**的人，预登记之后、判分之前改语料就是中途换被测物。
理由与逐份候选写在 `_ledgers/_署名证据的两个层次-2026-08-14.md` 末节。

不需要语料的那些**现在就该是绿的**，可以立刻验：

```bash
python3 CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline/assign_lanes.py --selftest
```
（应当打印「自测通过：书信 正 12／反 11 ＋ 画名 反 5／正 4 ＋ **自传 正 4／反 4**，全绿」并 rc=0）
★ 这一行的**预期输出是 2026-08-13 在一个真 clone 里跑出来抄的**，不是凭记忆写的。当天加自传规则时它变过一次（少了「自传」那一段），**文档里引用的输出会随工具漂**——对不上先跑一遍再判断是不是坏了。

★ 另一条也不需要语料，且**每次改过量测工具之后都该跑**：

```bash
python3 CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline/check_measurements_fresh.py
```
它把分道/分档工具在临时目录里重跑一遍，与仓里存着的产物逐字比对。
**修好工具不等于修好数据**——2026-08-13 实测有 4 个工作区的产物是旧版工具留下的。

**这两条恰恰是对的行为**——旧版本在这种情况下会打 ✓ 并 rc=0，
全库实测有 11 个工作区、264 条引文就是那样绿的。已修。

要跑起来，先把语料放回去（任选其一）：

```bash
python3 CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline/fetch_ia.py \
  --ids-file <工作区>/raw/_ids-rebuild.txt --out <工作区>/raw --skip-existing
```

或把另存的正文拷回 `<工作区>/raw/`（文件名要与台账 `local_path` 对得上）。

### ★ archive.org 不是唯一的通道（2026-08-14 新增）

`fetch_ia.py` 只走 archive.org。**捷克/中欧的材料它一份都看不到** ——
Comenius #182 因此被记成「通道受限」整整两天，而真相是词表漏了一个语种（见下）。

```bash
# 列（只列不下，不绕任何访问控制：只取 dostupnost=public）
python3 CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline/fetch_kramerius.py \
  --host kramerius5.nkp.cz \
  --query 'dc.creator:Komensk* AND fedora.model:monograph AND datum_begin:[* TO 1930] AND dostupnost:public' \
  --rows 10 --list
```

**取回来先看两个字段再决定用不用**：`fetch_kramerius.py` 每份记
`letter_run_ratio`（≥2 连续字母的词占 token 比）与 `ocr_verdict`。
实测同一天同一个馆：1892 那卷 **0.9256**（可用）／1882 那卷 **0.0000**（乱码），
而后者的 `words`／`pages_with_text` 看上去**比前者还健康**。
**「取回成功」≠「取回了能用的字」。**

### ★ 书信集不许整卷判 HIS-OWN（2026-08-14 新增）

```bash
python3 CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline/slice_letter_volume.py \
  <正文.txt> --from 0.05 --to 0.70 --decisions <裁定.json> --out <目录>
```

1892 Patera 卷实测：**121 封里他自己只有 96 封**，其余 24 封是他收到的信、
或**连他都不在场的第三方往来**（`Mr. Hartlib to Mr. Pell.` ×6）。
整卷当一手就是 [[related-to-him-is-not-written-by-him]]。
判不出方向的一律留 `?`，**不许当成他的**；人读定案要走 `--decisions`
且**每条必须带证据原文**（没有证据的裁定工具会 raise）。

## 四、★ 唯一的停点：阶段 5 判分

**8 个人**的产物与题目都做完了、**且合成门全过**，就差判分。判分要**两名互相独立的评委**。

    Lincoln  Jefferson  Bismarck  Pestalozzi  Machiavelli  Rousseau  Kant  Fröbel

★★ **8-13 当晚撤回过一次「11 人」**：Brandeis #172／Michelangelo #185／Dewey #190
当天被我登记成「等着判分」，而真跑合成门是 **22／46／36 条硬错**
（★ 8-14 凌晨已做掉一大半，当时现测 **8／19／13**，合计 104 → 40；**8-14 傍晚再测：Brandeis 8→5、Michelangelo 19、Dewey 13→2，合计 26**，逐条见诊断书）——
**产物齐 ≠ 过门**。他们要回阶段 3／4 返工，不是判分。
（其中两人当时连门都没开机：缺 `SKILL.md`，`quality_check` 直接报 `target.invalid` 拒检。）
详见开箱即跑清单开头那节「撤回」。

判分之前先跑一次就绪度（它**不覆盖合成门**，会明写要你另跑）：

```bash
python3 CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline/check_scoring_ready.py
```

★★ **它会印「真正等着判分的 17 人」并以 rc=1 退出 —— 那个红就是这个停点本身，不是坏了。**
上面写 8、判据印 17，**是两个口径，不是矛盾**：

| | 人数 | 谁 |
|---|---:|---|
| **第 1 批：预登记清单点了名的** | **8** | 就是上面那八个（lincoln-174／jefferson-175／bismarck-176／machiavelli-177／rousseau-178／kant-179／pestalozzi-180／frobel-181） |
| 有题、没分，但**不在第 1 批** | 9 | blackstone／blackwell／brandeis／churchill／cicero／dewey／kelsen／michelangelo／paton |
| **判据印的合计** | **17** | 它的口径是「**有用例 ＋ 没有判分结果**」，不问在不在第 1 批 |

**要判的是那 8 个**——分辨力、压线复核、逐人风险都**预登记过**（见开箱即跑清单）。
另外 9 人判据会在「缺件」栏逐条写明卡在哪（未预登记／缺 `SKILL.md`／延后名单里已结案
而产物齐全……）。**别顺手把他们一起判了**：判完再补口径就不是预登记了，
而本项目的规矩是「装置先落纸，判完只补实测数」。

合成门要逐人真跑（每人几分钟）：

```bash
python3 CodexSkills/registry/codex/persona-distiller/scripts/quality_check.py <工作区> --phase synthesis
```

「独立」在这里的意思**与任何特定产品无关**，只有三条：

1. **两个评委各自在一个全新的、空白的会话里工作**，互相看不到对方的输出；
2. **只给它们**：题目 + 两份待评答案（A/B 匿名）+ 那道题的评分标准；
   **不给**：人物档案、研究稿、工作区里任何别的文件、这份 START-HERE；
3. 两名评委的打分**分别落盘**，不许合并之后再看。

具体怎么摆、判读规则是什么，全部**预登记**在：

    CodexSkills/skill_log_evals/persona-distiller/_ledgers/_第1批阶段5判分-开箱即跑清单-2026-08-13.md

那份文件是**判分之前写的**（装置、已知风险、判读规则先落纸，判完只补实测数、不改口径）。
**照着跑就行，不要重新设计。**

## 五、接着往下做什么

> ★★★ **先知道一件事：队列里没有「下一个人」了。**
> `next_person.py` 现在输出 **`NEXT = None`**，`queue_pending = **0**`。
> **那不是坏了**，恒等式自己闭合：
>
>     queue_total 237 ＝ done 40 ＋ pending 0 ＋ deferred 185 ＋ 「已做但未出货」12
>
> 那 12 个人是 Brandeis／Marshall／Lincoln／Bismarck／Machiavelli／Jefferson／
> Michelangelo／Kant／Rousseau／Pestalozzi／Fröbel／Dewey ——
> **全部卡在阶段 5 判分或返工**，不是「还没开始」。
> ⇒ **接下来能做的事都在下面这张表里；「再挑一个新人物来蒸」不在其中**
> （要挑新人得先补队列，而那件事用户 2026-08-12 明确暂停了）。
>
> 现算：
>
> ```bash
> python3 CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline/next_person.py
> ```

按优先级：

1. **跑阶段 5 判分**（上面第四节）——这是唯一卡住的一步，**8 个人**，
   开箱即跑清单第一至六节。（第七节那三人已在开头「撤回」一节里排除。）
2. ★ **判分之前先跑一次就绪度**，它会把缺件、矛盾、压线一次列清：

   ```bash
   python3 CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline/check_scoring_ready.py
   ```

   ★ **它现在返回 `rc=1`，那不是坏了**——1 的意思是「有人缺件、没预登记、或存在矛盾」，
   这些正是要给人看的东西。**2026-08-14 现跑实测**：判据印「真正等着判分的 **17 人**」，
   其中带「延后名单里已结案而产物齐全」这条矛盾的是 **6 人**
   （blackstone／blackwell／churchill／cicero／kelsen／paton）。
   `rc=0` 才表示**那 17 人**全部就绪且无矛盾。**判分该不该跑由人定，这件判据不代替授权。**

   > ★ 这两个数原来写的是「5 个人」「11 人全部就绪」，**都是旧的**（真值 6 与 17）。
   > 上面第四节那张表里的 8／9／17 才是当前口径。要现算就直接跑上面那条命令看它自己印的分母。

3. ★ **Brandeis／Michelangelo／Dewey 回阶段 3／4 返工**（**2026-08-14 傍晚现测 5／19／2 条硬错，合计 26**；此前写的 8／19／13 是当天凌晨的数 —— Brandeis 当晚补了 1 条证据＋1 条 heuristic＋1 条 mental-model，Dewey 另有人做过。现算：`python3 CodexSkills/registry/codex/persona-distiller/scripts/quality_check.py <工作区> --phase synthesis`，
   逐条列在开箱即跑清单开头的「撤回」一节）。**不要送去判分。**
   ★ Dewey 另有一件判他分时要知道的：lanes 压线 3=3，撑起第三条道的只有一份
   与妻子共同署名的《Letters from China and Japan》（第七之二节）。
4. **不要再开 Churchill #191／Ford #188**：两人都已记延后，理由与解锁条件在
   `_ledgers/_延后名单.json`。Churchill 的产物做完了但**语料没过门**（见第四节 ★）。
5. ★ **不要重开已记延后的人**：第 2 批十人**九人出局**，死因与判法写在
   `…/_ledgers/_第2批结算-十人九出局-2026-08-13.md`；
   压倒性的第一死因是 `min_lanes`（六条研究道里有材料的不足 3 条），
   而这类人**语料量与一手占比往往远超门**——只看份数会以为可以做。

## 五之一、★★★ **判分之前必须先定的一句**（2026-08-14 发现）

**八人里四人的档位，`meta.json` 与「由材料现算」的结果不一致。**

| | 阶段 2 台账「判据给的档」 | 阶段 3 收尾表 | `meta.json` |
|---|---|---|---|
| Lincoln／Jefferson／Bismarck／Pestalozzi | **deep** | **deep** | `quick` |
| Machiavelli／Rousseau／Fröbel／**Kant** | quick | —— | `quick` ✓ |

★ **订正**：先写成「五人」并把 Kant 算了进去，**那是错的**——阶段 2 给他记「道 6」，
而 `_lanes.json`／台账／研究道**三处现测一致地说他只有 3 道**（阶段 2 那个数陈旧，
分道后来重测修正过）。**Kant 的 `quick` 站得住。是四人。**
那四人的 6 道也是三处交叉核过的，不是只看一处。

`quality_check` 与判分读的是 **`meta.json`** ⇒ **照现在跑，那四人按 `quick` 判**：
`min_baseline_delta` **0.03**，而台账说的 deep 是 **0.07**——**差 2.33 倍**
（`min_overall` 0.65 vs 0.80、`min_fact` 0.80 vs 0.93 同理）。

★ **我没有碰那 4 份 `meta.json`。** 改成 deep 会让他们更难过（方向上不利于我），
**但那仍然是「量之前动尺子」**，而判分清单的全部意义就是判读规则先落纸。
⇒ **判分之前先定一句：按 `quick` 还是按 `deep`。** 详见判分清单末节。

## 五之二、★ 新出现的一件「只能你定」（2026-08-14）

**「档位（profile）该按台账份数算，还是按去重后的独立作品数算？」**

- 现在 `min_sources`（quick 8／standard 24／deep 45）读的是**台账行数**。
- 而 8-14 全库重量实测：**42 个工作区里 36 个有塌缩**
  （Koch 120 份塌缩 17–25、Blackwell 89 份 13–25、Lister 60 份 14–19；
  表在 `_ledgers/_全库独立作品数重量-2026-08-14.md`）。
- 逐人核档位：**0 个确定掉档、3 个说不准**（Lincoln 是并查集串过头的假象；
  真压线的是 **Semmelweis 44–50／门 45** 与 **Lister 41–46／门 45**）。

★★ **为什么这条只能你定**：Lister 卡的是 `fact-preservation 0.8925 < 0.930`，
而 **0.930 正是 deep 的 `min_fact`，standard 是 0.88** ——
把他改判 standard，那一项当场变绿。**我没有改**，因为
① 这个测量是我引入的而改动恰好对结果有利；
② **这条线只救得了三个人里的一个**（Pasteur 0.8725／Koch 0.8050 都够不着），
   一个只救一个人的旋钮就是按结果拟合参数；
③ 规则一改是**全库口径变更**，同时动到已入库／已延后／待判分三批人。

详见 `FINDING_min-fact-threshold-above-seat-ceiling.md` 末节。

## 六、★★ 开工前必读的两份

1. **`文档/踩坑库/README.md`** —— **条数以它自己的首行为准**（2026-08-14 现测 **193** 条）。
   **这里有意不再复述那个数**：它每加一条就变，而复述出来的数只会越放越旧
   —— 这一行原来写「165 条」，实际已经是 193。要现算就跑：

   ```bash
   head -1 文档/踩坑库/README.md
   python3 CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline/check_lessons_library.py
   ```

   那件判据核的正是「README 首行的条数 ＝ 教训文件数 ＝ 索引条目数」三者一致，
   **且它接在移交包的回读自验证里**，所以首行那个数不会悄悄漂。
   **不是风格指南**，每一条都是一次真实的错判 + 可复算的数字 + 怎么提前发现。
   开工前至少读它列的那 10 条，能省掉一整轮返工。
2. **`HANDOFF.md`** —— 全部细节（**很长，按需检索，不要通读**；
   要知道多长就 `wc -c HANDOFF.md`——**别信这里写死的 KB 数**，
   这一行原来写 120KB，现测已是 127KB）。

## 七、几条不许破的规矩

- **零编造**：来源、事实、引文、分数。做不到就如实说做不到。
- **只取公有领域**：出版年 ≤ 1930（分界随年份滚动，代码里是 `PD_CUTOFF`）。
  付费墙不碰，访问控制不绕，验证码不绕。
- **`_protected/` 只增不减**：永不删、永不上传。
- **主树只读**：开发一律在 `git worktree` 里做。
- **推送到远端是人的动作**，助手不要自己推。
- **报数之前先跑命令**，不要凭记忆。管道会吃掉退出码，要判成败就别接管道。

---

★ 这份文件**只讲仓里的东西**：文件路径、`python3`、`git`。
没有任何一句话依赖某一家 AI 产品的功能。换任何一个助手接手，读完这一页就能开始。
