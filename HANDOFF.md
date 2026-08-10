# HANDOFF —— 接手这个仓要知道的全部

> 这份文件是**唯一入口**。一句话 prompt 只需把你指到这里。
> 写于 2026-08-10；每次移交前更新「现在做到哪」一节。

---

## 0. 先读这两份，其余都是细节

1. `~/Documents/Codex/GithubProject/README.md` 的 **「七条铁律」**（第 23 行起）——
   本机所有仓共用的硬约束。**代价最高的三条**摘在下面第 5 节。
2. `CodexSkills/skill_log_evals/persona-distiller/_ledgers/_每次开工必读.md` ——
   这个项目自己的开工必读。

---

## 1. 这个项目在做什么

**人物蒸馏（persona distillation）**：把一个真实人物的公开材料，
蒸馏成一套可被 AI 扮演的产物（十份 Markdown + 断言层 + 用例集），
并用**盲评**测出它比裸模型好多少（`delta`）。

- 目标规模 **600 人**，分 **12 个职业族**。
- **只取公有领域材料**；付费墙一律不碰；不绕任何访问控制、不绕验证码。
  「开放获取」**不等于**公有领域。
- 每个人物走同一条流水线，**每一步都有判据（checker）把关**。

---

## 2. 现在做到哪（**更新这一节，不要更新别处**）

- **已入库：102 个产物**（2026-08-11 实测）。★ **要报这个数就当场跑一遍**，不要抄这一行：
  ```bash
  python3 -c "import json;print(len(json.load(open('CodexSkills/registry/codex/persona-distiller-group/team-index.json'))['products']))"
  ```
- **延后／拒发名单：139 条**（2026-08-11 实测），其中 **75 条**带 `pd_scope_pending`（等待裁定 ㉜）。
  ★ **列表的键是 `deferred`，不是 `items`/`entries`**——写 `d.get("items") or []` 会**静默返回 0**，
  我 2026-08-11 差一点把这个 0 写进本节。**取不到就让它炸，别给空默认**：
  ```bash
  python3 -c "import json;d=json.load(open('CodexSkills/skill_log_evals/persona-distiller/_ledgers/_延后名单.json'));i=d['deferred'];print(len(i), sum(1 for x in i if x.get('pd_scope_pending')))"
  ```

### 2026-08-11 这一天（**接手前最后一批改动，都在判据层**）

- **#165 Walter A. Shewhart 已入库**（第 102 个，v0.0.0.1，财务合规师族）。
  delta **+0.1822**、两席同号 16/16、四道门全过；★ 但预登记要求的单列改了结论——
  抽掉「候选有文献而基线没有」的 3 个套组后剩 13 题只有 **+0.0812 / 1.71 SE**，
  判为**不进第 2 轮**（结构性限制，不是噪声）。他也是**全库第一个 `capability_evidence: true`**。
- **#168 Hugo Grotius 开工**（政治法律师，1583–1645）。同名护栏已过
  （`ready/single/grotius-hugo-1583`），**12 个候选里 3 位只靠一个特征才分得开**；
  抓源在跑。★ 开工须知全在 `_corpora/wip-grotius-168/00-同名判定.md`，
  探测在 `_corpora/_探测记录/168-grotius-可得性探测.md`。
  **最要紧的一条：不要用 Campbell 1901 译本量声口**——它只有 Kelsey 1925 的 36% 长、
  整章没收 Prolegomena，密度会低 **130 倍**（0.007 vs 0.85 每千词），差点据此记了延后。
- **四处判据缺陷，都是「门是绿的而它根本没在查」那一类**：
  1. **交接文档的第一条命令跑不通**（`namesake_gate.py <人名>` 而工具要 `--name`）。
     已落成 `check_handoff_commands.py`（接进 `finalize_release.py`）。
  2. **内容层三项检查在每一次打包里都没跑过**：`package_target.py` 跑
     `quality_check --strict` **不带 `--cache`**，而「未做」不算 warning。
     已改成自动用 `<工作区>/raw`，两者都没有时记 warning。
  3. **`check_claim_coverage` 的 join key 两边算法不一样**：台账存 `sha256(原始字节)`，
     判据算 `sha256(剥表头后的正文)` → 四个带抓源表头的工作区**一条都回连不上**。
  4. **`check_verdict_attribution` 只扫一层**，真值集少了一个人（96 → 112）。
- **全库装饰性引用射程已量清**（`_ledgers/_装饰性引用射程-2026-08-11.csv/.md`）：
  29 个工作区**全部可量**，干净 25、有装饰性引用 4，
  **102 个已交付产物里一个都不涉及**。
  ★ 这个数是**四步**才稳下来的，中途报出的「5 个回连不上、6 个无 raw/」**全是假象**。
- ★★ **6 个工作区的路径重了一层**：`wip-X/workspaces/<slug>/<slug>/`
  （Barton #117 / Fleming #111 / Nightingale #112 / Osler #110 / Sorby #133 / Virchow #109）。
  **glob `workspaces/*/` 拿到的是只含内层的空壳。**
  目录本身没动（都是已归档件，移交前不做大改动），改的是工具的射程——
  写新工具时**两层都要扫**。

- **更早做完的**：
  - **#156 Henry Gantt 记拒发**——真 delta **+0.0078**，quick 门 +0.03，**两席跨零**
    （F −0.0125 / G +0.0281）。判决书 `_corpora/wip-gantt-156/workspaces/henry-gantt/evals/00-结案.md`。
    ★ 盲判装置是至今最干净的一次：均长比 1.01、**「候选更短 ≥25%」首次通过（7/16）**、
    九种表面特征两侧全 0/16。
  - **#157–#160 建造采购师四人一次判掉**（Kelley/Walker/Oliver/Hau Lee）——
    判据是**出版年**晚于 1931 分界，**第二个被 PD 规则清空的族**。
  - **#161 Luca Pacioli 记延后（新类别⑦：方法证据全部汇到一部作品）**。
    ★ **这一条值得读，因为它不是「语料不够」**：10 份源、294 万字符、全部公有领域、
    全部读得到、研究门 passed、断言层 14 条逐字引文预检全过——
    **而他的记账论述只存在于一部作品**，三份译本只算一处证据，
    于是「方法类断言要 ≥2 处独立证据」诚实地只满足到 **1 个 mental-model ＋ 1 个 heuristic**
    （门要 2 和 3）。判决书 `_corpora/wip-pacioli-161/workspaces/luca-pacioli/references/research/00-处置.md`。
- **#162 William Andrew Paton 记延后（新类别⑧：盲判装置不成立）**，**评委一次都没派发，没有产生过任何分数**。
  详见下面那一大段，以及 `_corpora/wip-paton-162/.../evals/00-结案.md`。
- **#163 A. C. Littleton 记延后（新类别⑨：成名作全部落在 PD 分界之后）**——**开工前量的，一份源都没抓**。
  ≤1930 已核过出版年的一手材料 **7 份**（1 本入门教材 ＋ 6 篇《The Accounting Review》论文，122–134 页），
  `min_sources` 门要 8 差 1 份；**而 `min_lanes` 3 是硬卡点——7 份全是 writings，另五道各 0**。
  ★★★★ 真正的理由：他 7 部著作出版年 **1933–1965，没有一部 ≤1930**
  （《Accounting Evolution to 1900》是 **1933**，书名里的 1900 是**内容年代**不是出版年）。
  **与 Nowlan #155 不同：Nowlan 生得太晚，Littleton 是成熟期太晚**——
  可取得的那部分**不是他之所以是他的那部分**。
  ★ 同名护栏已备好，重启不必重查：**`Ananias` 是极罕见教名**，比生卒年更可靠；
  地名里风险最高的是 **Littleton, Illinois**（州名会与 University of Illinois 同时出现）。
  探测报告 `_corpora/_探测记录/163-littleton-可得性探测.md`。
- **#164 Herbert Heinrich 探测中**（1886–1962，事故三角形）。
  ★ 他的代表作《Industrial Accident Prevention》通行说法是 **1931**——
  **若确是 1931 就差一年**，`2027-01-01` 才进入公有领域（PD 分界每年元旦前移）。
- **【已作废】在办：#162 Paton**（下面这段保留是因为它记着装置层的实测，判决见上）。
  工作区 `_corpora/wip-paton-162/workspaces/william-andrew-paton`（**单层，不是双层嵌套**）。
  - **研究门 ✓ 合成门 ✓（均 0 错）**；24 份来源 / 22 部作品；三道齐；
    **13 条断言（mental-model 2 / heuristic 3，quick 档最低数达标）**；
    **十份产物写完，51 条引文 0 未命中**；18 题用例；**4 份 holdout 正文已移出 train 目录**。
  - **卡在第 1 轮盲判的装置上**，**三次**被自己预登记的规则拦下：
    ① **引文坐标门**（硬门）：候选侧 11 条长引文无坐标 → 产物补了 29 处坐标，重跑候选。
    ② **规则 4 均长比**：候选/基线 = **1.28（v1）／1.77（v2）**，界是 0.8–1.25；
       「候选更短」只有 **6%**，界是 ≥25%。
       ★ **坐标不是原因**——所有坐标括注合计仅 588 字符（每题 33 字），扣掉后仍 1.71。
       **候选侧读了产物就是会写得更长。**
       → 两侧同加「每题 350–650 字」重跑（v3）。
    ③ ★★★★ **规则 4 的格式项：反引号 17 : 0**（界 ≤4）。
       **先问了「去掉记号，线索还在不在」——还在**：
       剥掉全部反引号后，**≥5 词连续英文 15 题 : 0 题**、≥8 词 11 : 0、
       引文坐标 13 : 0，**基线侧 18 题里一段英文都没有**。
       **改排版救不了**——破盲线索是「能出示一手逐字引文＋坐标」这件事本身，
       而那正是本产品的立身之本。★ 这是**待裁定 ㉓** 迄今最干净的一次实测。
       → 两侧同加「用自己的话作答，不出示逐字引文、不写出版坐标」重跑（v4）。
    - ★★ 顺带查出**我自己预登记时的一个缺陷**：规则 4 **没写明字数按什么口径**。
      同一批答案两种口径给出**相反**结论：总字符 1.206 / 候选更短 6%（✗）；
      汉字 0.838 / 候选更短 89%（✓）。差异全来自候选嵌入的英文引文。
      ★★★ **没有去选那个能过的口径**——看过结果再定规则就是造假。
      本轮按「两个口径都要过」处理（即不过）；口径定义补给**下一个人物**用，不追溯。
  - ★★ **已跑的次数如实记在 `evals/第1轮-协议记录.md` 的三条偏离记录里**：
    到 v4 为止**基线 3 遍、候选 4 遍**，**每一次都不是因为答得不好，也没有据此挑**。
  - ★★★★ **协议里已写死：v4 是最后一次重跑。**
    若仍不过规则 4，**记延后，理由「盲判装置不成立」，不派评委、不产生任何分数**。
    永远变不绿的红不该反复去撞。
  - ★★★ 这是**待裁定 ⑤**（长度混杂／格式门与长度门互相拉扯）的新实例。
- **#161 Luca Pacioli 记延后**（新类别⑦：方法证据全部汇到一部作品）。判决书
  `_corpora/wip-pacioli-161/workspaces/luca-pacioli/references/research/00-处置.md`。
- **本轮新落的判据**：`check_translation_witness.py`——
  **同一部作品的多个译本不许当两处独立证据**。
  根因：`check_claim_source_independence` 的作品分组**是语言盲的**，
  实测把 Pacioli 的 10 份源分成 10 个作品组，而其中三份译的是同一篇论著。
  ★ 它的「自动认出哪些是译本」那一半**实测做不出来，已砍掉**（全库误报 38,368 对），
  文件头留了数字，别再建一遍。
- ★★★★ **本轮修了三件会让你误判的东西，接手前务必知道**：

  1. **`next_person.py` 的 NEXT 一直是错的人。**
     默认 `--registry-root` 写死在一个**不存在的 worktree** 上，
     于是 `registry_products` 记成 **0**（真值 101），**20 个已入库的人被当成没做**，
     NEXT 从 `Barbara Liskov` 变成了 `Comfort Avery Adams`。
     已改成**从 `__file__` 推仓内路径**，并**每次打印实际用了哪三份路径**。
     ★ 队列与延后名单的旧默认在 `~/Downloads/蒸馏/`，**那不在 git 里**——
     移交之后你拿不到，所以必须走仓内那份。

  2. **`check_claim_source_independence` 的「证据塌缩」多报了 62%。**
     它用并查集（**传递闭包**）判「同一部作品」：A↔B 0.35、B↔C 0.35 就把 A 与 C 判成同一部，
     而 A↔C 实测可以是 **0.000**。Lister 因此被串成一个 **32 份**的分量（占 52%）。
     全库 **60 条 → 23 条**（Lister 17→0、Osler 4→0、Pasteur 5→0、Virchow 7→0、Jenner 3→0 全是误报）。

  3. ★★★ **语料文件顶上那段出处表头，判据一直当成他的话在读。**
     只有 **Adams（144 份）与 Coffin（36 份）** 有这种表头
     （`SOURCE:` 开头、一整行 `=` 收尾），占全文**聚合 17.2% / 11.7%**、**逐份中位 39.1% / 16.1%**。
     后果实测到三件：
     - `check_ocr_language_death` @ Coffin 不剥时报「每一份都在下限之上」，
       剥掉后报出 **2 份 0.101**（下限 0.15）——**我那段干净英文把 OCR 烂掉的文件托过了及格线**；
     - `check_lane_quotes_verbatim` @ Coffin 报出 `Coffin, Charles L., Detroit, Mich.` **对不上**——
       那句「逐字引文」**只存在于表头里**；
     - Adams 重复源 18→0、膨胀 1.327→1.0、断言塌缩 6→0。
     已建 `common.corpus_body()` 并接进 **16 个**判据。
     ★ **表头本身不要删**——出处、权利依据、同名者排除依据都在里面。
     ★★ `check_authorship` 一族**有意没接**：表头对它们是**署名证据**，
     那正是 Barton 事故所在（`# title:` 头被读成署名证据 11/14），**要专门一轮再动**。

  4. ★★★★ **台账的 `title` 有 99% 就是文件名。**
     全库 **1,943 / 1,969 行**，真书目题名只有 **26 行**（其中 25 行在 Martens 一个工作区）。
     后果不是难看：判「两份是不是同一部作品」时**除了内容重叠没有第二个证据源**——
     **全库剩下的 931 对未声明重复源清不掉，根子就在这**；
     引文坐标与「挂到哪部作品」也全落在文件名上。
     ★ 与空字段反过来：**空值至少诚实，填成文件名的字段看起来是填过的**，判据从来不报它。
     已建 `check_title_is_not_filename.py` 并接进 `quality_check --phase research`，
     **只报不拦**（99% 如此，硬门只会让人去关门）。
     回填照抄 Martens 的格式：**题名 ＋ 卷次 ＋ 出版地 ＋ 出版者 ＋ 年**。
     ★★ **这是抓源侧的活**，台账层补不出来。

- **待用户裁定的条目**：**读 `registry/codex/persona-distiller/references/ledgers/_待用户裁定.md`**（三十五条，每条都带「你选一个，我就照做」的选项）。
  ★★ **不要看任务列表**——任务表不跟着仓走，移交之后你根本读不到它。
  2026-08-10 核对时发现 **㉛㉜㉟ 三条只活在任务表里、台账里没有章节**，已补写；
  其中 **㉜ 已经挡着 75 人**。同一个教训 `_受阻待裁.json` 吃过一次。
  ★ 人物级受阻（做完或做到一半、卡在只有你能拍板的事）另见 `_ledgers/_受阻待裁.json`。
  **这些不是你能自己决定的**，遇到就停下来问。
  ★ **㉜（PD-only 规则的射程）**：延后名单里 `pd_scope_pending` **75 人**，
  而剩余队列里生年 <1913（可能可做）的还有 **62 人**——**队列没被规则耗尽**。
  ★★ **订正（08-10 按生年算过）**：那 75 人里 **71 人 1931 年时不满 19 岁**、
  **1931 年时已满 19 岁的是 0 人**。㉜ 现在摆的三个选项都不改 `≤1930` 这条门槛本身，
  **而那 4 个「生年未记」的（Kelley/Walker/Oliver/Hau Lee）是按出版年延后的
  （CPM 1959、1982 年访谈、现任教授），同样晚于分界** ——
  **所以 ㉜ 按现在的三个选项，能解锁的人数是 0，不是 75，也不是 4。**
  （这个数我当天改了三次 75→4→0，每次都是没把最后一步算完就报了数。）
  真正挡着这 75 人的是另一个问题
  （台账里记作 **㉜′：`≤1930` 这条门槛本身要不要保留**）。
  **这些延后都是可一行反转的**，不要因为它没裁定就停下来。
  ★ **㉝ 是本轮新增**：`status: hypothesis` 在流程里没有落脚点，
  门对它与 `pattern` 一视同仁地要 ≥2 处来源。
  ★★ **㉟（2026-08-10 新增，最要紧的一条）**：**写 rubric 的人与写候选答案的人是同一方。**
  实测（rubric 的 4-gram 减去题面回声后在两侧的命中率）：
  **Thomson +37.1% / Carver +23.9% / Cicero +7.7% / Sorby +0.1%，7/7 全为正**——
  这是「产物 → 用例集 → 候选答案」流程顺序的**结构性产物**，不是某个人的毛病。
  ★ 但它**预测不了 delta**（Thomson 回声最高而 delta −0.0859），**别把它当成万能解释**。
  判别实验：**候选答案改由没看过 rubric 的一方写，rubric 与基线一字不动**。

- **2026-08-10 又做了四人 + 三件判据**：
  - **#163 Littleton 记延后（类别⑨：成名作全落在 PD 分界之后）**；
    **#164 Heinrich 记延后（类别⑩：代表作差一年，2027-01-01 自动解锁）**。
  - **#165 Shewhart 探测完成**：首版 1931 差一年，但 **≤1930 已核实可免费全文 8 份、约 210 页**
    （BSTJ 六篇 1924–1930 + 1914 硕论 + 1922 PNAS）。
    ★★★★ **「恰好 8 份 = 下限，零余量，可以做」这句话 08-11 已被证伪——真实下限是 9，8 份走不完。**
    见下面 08-11 那条。报告在 `_corpora/_探测记录/165-shewhart-可得性探测.md`。
  - **#166 Cicero 全流程做完，第 1 轮 delta +0.2428（6.24 SE）——★ 不作数**。
    定案理由是**两席互不知情却点了同一批 rubric 缺陷，且 delta 最高的四题正是它们点的那四题**。
    判读在 `_corpora/wip-cicero-166/.../evals/00-第1轮-判读.md`（含我自己下错又订正的那条因果）。
  - **三件新判据／新模式**（都带正反自测，都已接进门）：
    1. `check_filename_year_vs_ledger.py`——文件名年份 vs 台账 `published_at`。
       全库 **28 条差 ≥2 年**；**Semmelweis 一人占 23 条**，读了 2 条题名页 2 条都是台账错，
       且 `published_at` 与 `locator` **同时挂到了另一份源上**。**PD 合规不受影响**（无一跨 1931）。
    2. `check_persona_frame_break.py --rubrics`（**不需要 answers**）——
       在**派发之前**验 rubric 有没有把「谈资料库」写成得分条件。已接进合成门。
       第一次跑就红了我自己 3 条。
    3. `declare_source_dedup.py` 的后缀表**补了语种标记**（前提：台账明写两侧同语种才剥，
       `x-de` ↔ `x-en` 必须判为不确定）。Virchow：机械上确定 0 → 8 对，未声明 126 → 118。

- **2026-08-11**：**判据的下限写错了两年，今天才有人撞上**
  - ★★★★ **`min_sources` 数的是 train，而合成阶段强制要有 holdout——holdout 要从总数里扣。
    所以真实下限是 `min_sources + 1`：quick 8→**9**，standard 24→**25**，deep 45→**46**。
    没有任何地方写着这个数。**
    Shewhart #165 一手正好 8 份：留 0 份 holdout 则研究门绿、合成门必错；
    留 1 份则 train 掉到 7、三个阶段全错。**结构上无解。**
    代价不是多跑一次门——**研究门放行之后人会把十份产物全做完**，
    才在合成门上撞见 `source.no-holdout`，而要补的是材料不是文字。
    → 新判据 `check_corpus_feasibility.py`，在**研究阶段**就报 `corpus.structurally-infeasible`
    并算出**还差几份**。全库 **17 绿 / 6 红**，红的 6 个里 5 个是已知受阻的人，
    **所有已判分出货的人全绿**（正对照成立，不是恒红的门）。
  - **`check_authorship.py` 两处盲区**（Shewhart 撞出，全库前后对比验证）：
    ① **被 OCR 打坏的不止名字，还有 `By` 本身**（`Br W. A. SHEWHART`）；
    ② **期刊署名只印首字母而姓被打坏**（`By W. a. Shbwhart`）。
    ★ 修的过程里自己踩了两个坑，都写进自测了：
    **把 `y` 写进 OCR 混淆集**，于是干净的 `By ` 也算被打坏，下游闸门恒真——
    判据自带的 Fleming 同名负对照当场回归（`By A. Grant Fleming.` 被放行）；
    **首字母没要求带点**，于是德文正文 `von —10° R noch nicht schmerzhaft war`
    被读成 Robert Koch（`noch`↔`Koch` 距离 1）——**全库对比才照出来，自测没抓到**。
  - **`BYLINE` 的署名前缀只有英文 `By`**，而兜底那条的 `starts_by` 早就是多语的。
    实测同一形态：`By A. Martens` ✓ / **`Von A. Martens, Berlin.` ✗ 且兜底也 ✗**——
    而那是 Martens **最常见的印本署名**。两份清单已合并成一份。
  - **教训库仓内副本落后**：8 个文件内容不同、缺 1 条；`_索引.md` 手写的，
    写完当天就漂（头部写 113 而实际 115，摘要停在两版之前）。
    → 已同步，索引改成 `_生成索引.py` **现算**，带 `--check`。

- **2026-08-11 下半场：#165 Shewhart 从「结构上不可能」走到 release 门只差判分**

  | | 早上 | 现在 |
  |---|---|---|
  | 一手 | 8（真实下限 9，**无解**） | **13**（12 train + 1 holdout） |
  | 道 | 2 | **4**（writings 7 / decisions 3 / conversations 1 / external 1） |
  | 研究门 | 13 错 | **0 错 0 警告**（24 条引文全部对回原文） |
  | 合成门 | — | **0 错 0 警告** |
  | release 门 | — | **1 错**：`eval.no-results`（盲判还没跑） |

  ★★★ **解开它的是重新 OCR。** ASCE Transactions Vol.91 (1927) 里有他的讨论发言
  （`conversations`）＋ 对手的答辩（`external`）——**一份材料同时解两道**，
  而 archive.org 那一卷的 OCR **系统性丢虚词**（≤2 字母词占比 **0.0265**，正常散文 0.25–0.28，
  且元数据**自报 confidence 94**）。用 macOS Vision 重 OCR 原生页图（2236×3448）后 **0.3331**。
  工具与判读法在 `scripts/tools/vision_ocr.m` + README。
  **★ 不要用 Swift 写它**（Command Line Tools 重建 swiftinterface 会失败）；ObjC 一次就过。

  ★★ **切段的两条铁律**（都是实测踩出来的，写在那份 README 里）：
  **起讫由发言标签定不由书眉定**（p.50 书眉写 SHEWHART 而前 37 行是前一位的尾巴，
  p.54 书眉写 NIMMO 而他的话还延续 19 行）；
  **剥版口只剥「书眉 + 紧邻的那个数字」**（第一版把表格里的 `779`/`673`/`953` 一起吃掉了）。

  ★ **两个数一起记**：一手来源总数 **13**（门数的是这个），
  而按「内容必须承载他为人所知的方法」那把尺子只有 **8**——
  1914 涟漪波、1917 黏性介质小液滴、1919 教学随笔都是物理。**不选一个报。**

  下一步：两侧答题已派发（候选方**只读十份产物、不许碰 `evals/`**；基线方**什么都不给**）
  → `build_blind_payload.py` → 两席评委 → `assemble_judge_results.py`。

---

## 3. 怎么跑

所有工具在 `CodexSkills/registry/codex/persona-distiller/scripts/`。

```bash
cd CodexSkills/registry/codex/persona-distiller
```

★★★★ **下面每一条都能照抄**（只把 `<...>` 换成真值）。
**尖括号是占位符，其余一个字都别改**——尤其别把 `--name` 去掉写成位置参数。

> 这一节 2026-08-11 之前是错的：写着 `namesake_gate.py <人名>`，
> 而工具要 `--name <人名>`，**接手方照抄的第一条命令就会报错**。
> 另有四条用 `…` 带过参数，等于没写。
> 现在有判据管着，**改完这一节必须跑一遍**：
> `python3 scripts/check_handoff_commands.py`（在仓根跑，`--all` 扫全部 handoff 文档）。

```bash
# ① 下一个做谁（★ 先看它 stderr 打印的「实际用的路径」那一节）
python3 references/pipeline/next_person.py

# ② 同名护栏（★ 是 --name，不是位置参数）
python3 scripts/namesake_gate.py --name "<人名>" --output <护栏结果.json>

# ③ 建工作区（三个必填：--name / --identity / --namesake-gate）
python3 scripts/init_target.py --name "<人名>" --identity <identity.json> \
    --namesake-gate <护栏结果.json> --profile quick --workspace <工作区目录>

# ④ 灌语料（两个位置参数：工作区、一个或多个输入文件）
python3 scripts/ingest.py <工作区目录> <语料文件> --tier P1 --dimension writings \
    --author "<人名>" --published-at <年份> --locator "<页码/卷期>"
#    ★ holdout 那一份加 --holdout；synthesis/release 阶段**强制**要有 holdout，
#      所以真实来源下限是 min_sources + 1。

# ⑤ 三道主门
python3 scripts/quality_check.py <工作区目录> --phase research
python3 scripts/quality_check.py <工作区目录> --phase synthesis
python3 scripts/quality_check.py <工作区目录> --phase release

# ⑥ 造盲判载荷
python3 scripts/build_blind_payload.py --workspace <工作区目录> --round-dir round1 \
    --candidate <候选答案.json> --baseline <基线答案.json> --baseline-source bare-model-run

# ⑦ 汇总判分（★★ baseline-source=bare-model-run 时**必须**给运行记录，否则 exit 3）
python3 scripts/assemble_judge_results.py --workspace <工作区目录> --round-dir round1 \
    --key <盲态key.json> --baseline-source bare-model-run \
    --baseline-run-record <round1/baseline-run-record.md>

# ⑧ 打包 / 入库（都是位置参数）
python3 scripts/package_target.py <工作区目录> --product-version 0.0.0.1
python3 scripts/register_persona.py <打包出来的.zip>

# ⑨ 声明重复源（★ 默认 dry-run，看过再 --apply）
python3 scripts/declare_source_dedup.py <工作区目录>
```

★★★★ `declare_source_dedup.py` **默认只写「机械上确定」的那一类**
（去掉来源后缀后词干相同＝同一件的另一份副本）。
**其余只列出来给人读，不写。** 这不是保守，是实测：
Nightingale 465 对里**只有 48 对是确定的**，其余 417 对包含
`royal-commission-report-1858` ↔ `mortality-british-army-1858`（0.44）这种
**跨作品的真实重印**——皇家委员会报告收录了她的 Notes，两者确实大段相同，
**但不是同一部作品**，方向靠干净度猜必然出错。
★ Blackwell 61 对一次做完（全对）**是个例外，别当通例**。

### ★★★★ 清重复源的**唯一站得住的做法**（2026-08-10 在三个工作区上验过）

**「同一部作品」= ① 题名页证据相同 ∧ ② 直接 8 词片重叠 ≥0.30。两条都要。**
两条必须**来源不同**：一条是印刷者的声明（题名页），一条是文本本身。
**只有一条时不写**——Jenner 那 13 对就是只有一条，负对照打掉后当天撤回。

```bash
# 核验一个题名/版次假设在不在题名页附近（**是/否**，可做正负对照）
python3 scripts/propose_title_from_titlepage.py --workspace <ws>         --filter <文件名子串> --verify-title "TITLE AS PRINTED"
# 读一遍命中的片段，确认无误再加 --apply
```

★★★ **是「核验一个假设」，不是「抽出题名」。** 抽取实测 **2/9**
（蔵書印／献词页／目录条目／出版者行全会被认成题名，黑名单永远补不完），**已砍**。
核验实测：Osler **13/14**、Barton **11/12**、Nightingale `NOTES ON NURSING` **30/37**。

★★ **OCR 讹字用「换短锚点」解决，不许放宽成模糊匹配**（那会让「像」当成「是」）。
实测撞到过：`THE PRINCIPLES AxVD PRACTICE`（AND→AxVD）、`aHE RED CROSS`（T→a）、
`A HISTORY OF THIS` 整段被毁（前后两词间只剩 25 个字符）。

★ 三个工作区的实测差别很大，**别把一处的成功当通例**：
英文题名页版次声明 Osler **10/14**；德文 `Auflage` Virchow 只 **4/26**（Fraktur OCR 更烂）；
Barton 的 7 份**一个版次声明都没有**（那书不带版次号）——**那时改用书名或版权声明**。

★★★★ **它最有价值的一次用法是「分开」而不是「合并」**：
Barton 的 `rc-peace-war` ↔ `rc-history` 跨族重叠 **0.922**（高于族内最低 0.800），
**单靠重叠必然合并**；而题名页干净地分开了两族——
真相是同一作者把 1898 年那本大段重用进 1899 年那本。

★ **NEXT 一律以 `next_person.py` 的输出为准**，不许凭记忆或凭队列文件里的顺序。
★★★★ **但先看它打印的「★ 实际用的路径」那一节。** 2026-08-10 之前它的默认仓根
写死在一个**不存在的 worktree** 上，于是 `registry_products` 记成 0（真值 101）、
**20 个已入库的人被当成没做**、NEXT 指向了错的人。现已改成从 `__file__` 推仓内路径，
并且**读不到 team-index 时记 `null` 而不是 `0`**。
★ 若那一节里 `有没有退回仓外的旧路径` 有任何一项是 `true`，**停下来看一眼**——
旧路径在 `~/Downloads/蒸馏/`，**那不在 git 里，你多半拿不到**。

★★ 每个 `check_*.py` 都有 `--self-test`。**改判据之前先跑它，改完再跑一次。**
判据自己也会错——本项目里判据的第一版出错是常态，不是例外。
★★★★ **而 `--self-test` 全绿不等于能跑。** 2026-08-10 实测两次：
- 我批量给 14 个判据加了一行，**自测全过**，而其中两处改成了 `a.corpus_body(...)`，
  **真跑就是 AttributeError**——自测碰不到那两条路径。
- 镜像树 `references/pipeline/checkers/` 里三个判据 `ModuleNotFoundError`，
  而 `check_contract_drift` 报「无漂移」（**它只比字节，不管跑不跑得起来**）。
**改完必须拿真工作区跑一遍，而且不要接管道**——
`python3 x.py | tail` 的退出码恒为管道末端的，不是脚本的。

---

## 4. 数据在哪

| 东西 | 路径 |
|---|---|
| 判据与工具（**唯一真源**） | `CodexSkills/registry/codex/persona-distiller/scripts/` |
| 判据镜像（合同：`check_*.py` 与上面**逐字节相同**） | `.../references/pipeline/checkers/` |
| 人物工作区 | `CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-<名>-<编号>/` |
| ★ 工作区的**真实层级**要用 `find … -path '*/evidence/claims.jsonl'` 定位 | 见下 |
| 名册（已入库的人） | `CodexSkills/registry/codex/persona-distiller-group/` |
| **台账**（队列 / 延后名单 / 卒年 / 额度 / 决策） | `CodexSkills/skill_log_evals/persona-distiller/_ledgers/` |
| 已交付的 44 个 zip | `CodexSkills/skill_log_evals/persona-distiller/_ledgers/*.zip` |
| **★★★★ 教训库（101 条实测事故）** | `CodexSkills/skill_log_evals/persona-distiller/_ledgers/_教训库/`，**入口是 `_索引.md`** |

### ★★ 工作区层级：有三个人是**双层嵌套**，别猜路径

`_corpora/wip-osler-110/workspaces/william-osler/**william-osler**/`（Nightingale、Virchow 同）；
而近期的人（Gantt、Nasmyth、Pacioli）是单层。
**根因是 `init_target.py --workspace` 会自己追加 slug**——
传 `.../workspaces/<slug>` 就会变成 `.../workspaces/<slug>/<slug>`，
**要传 `.../workspaces`**。

**所以定位工作区一律用：**

```bash
find CodexSkills/skill_log_evals/persona-distiller/_corpora -path '*<slug>*/evidence/claims.jsonl'
```

### ★★ 抓源方**不要**把下载件写进 `raw/`

`ingest.py` 会把每份源**复制两处**：`raw/src-<id>/<名>.txt` 与
`references/sources/src-<id>/<名>.normalized.txt`。
所以如果抓源方直接把原件下载到 `raw/`，灌完之后 `raw/` 里会同时有
`raw/<名>.txt` 与 `raw/src-<id>/<名>.txt` —— **同一份文件两次**。

**给抓源子代理的指令里，落盘目录要写工作区外的暂存目录**（或 `_staging/`），
灌完再删暂存。2026-08-10 我给 Pacioli 的指令写成了 `raw/`，
于是那个工作区成了全库 28 个里**唯一**有同名冲突的一个
（文件 17 份、按 basename 去重后 10 份）。

★ 路径猜错时判据会老实返回 `状态: …未核验（不是通过）`——
**但只有你把 `状态` 字段打印出来才看得见。** 2026-08-10 我因此差点把「没核过」记成「修好了」。

★ 台账原本只在 `~/Downloads/蒸馏/`，**2026-08-10 搬进仓**。
`next_person.py` 现在**仓内优先**；两处都在且内容不同时，它会把两边的 sha256 与 mtime
打到 stderr 上——**看到那段就先弄清哪一份是对的，别当没看见。**

---

### ★★★★ 处置有**三种**状态，三份机器可读的文件，别只看两份

| 状态 | 文件 | 现有条数 | 含义 |
|---|---|---:|---|
| 已入库 | `registry/codex/persona-distiller-group/team-index.json` 的 `products` | **101** | 做完并注册 |
| 延后／拒发 | `skill_log_evals/persona-distiller/_ledgers/_延后名单.json` | **135** | **我判的**：够不着门、材料不可得 |
| **受阻待裁** | `skill_log_evals/persona-distiller/_ledgers/_受阻待裁.json` | **3** | **我判不了的**：只能由用户拍板 |

**核对命令**（第一步就跑）：

```bash
python3 CodexSkills/registry/codex/persona-distiller/scripts/check_disposition_exclusive.py
```

★ 它落成当天第一次跑真数据就抓到两条：**Steinhardt 与 Godin 同时在「已入库」和「延后名单」里**
（是我把已交付的人错加进了延后名单，已移出，137 → 135）。

### ★★★ 还有第四类：**跨人物的长期工程待办**

`_ledgers/_长期待办.json`（5 条）。**它同样是 2026-08-10 才建的**——
其中「本机 skill 副本落后」这一条，核对时**在整个仓里 0 处提及**，只活在会话任务表里。
每条都写了 `done_when`（怎么判断它做完了）与 `blocked_by`。

★ **第三份是 2026-08-10 移交前才建的。** 在那之前这个状态**只活在会话的任务表里**，
而任务表不跟着仓走——核对时发现 Adams／Martens／Roberts-Austen 三人
**既不在名册也不在延后名单**，接手的人会把他们当成「从没碰过」。

★★ 用户裁定之后，把人**从受阻名单挪走**（入库进 team-index，判不做进延后名单），
**别让同一个人同时留在两处**。

---

## 5. 三条最贵的铁律（全文见 GithubProject/README.md）

1. **主树只读，开发一律在 worktree。**
   `GithubProject/<REPO>/` 永远停 `main`、永远干净、只 `git pull` 不写。
   ```bash
   git worktree add ../_scratch/<repo>-<任务名> -b <分支名> origin/main
   ```
2. **谁开的谁收。** 代码合了 + PR 关了 + worktree 收了 + 分支删了 + 缓存清了，**五件缺一不算完成**。
   清缓存用 `git gc`，**禁止 `--prune=now`**（有线程因此丢过 2467 个提交且不可恢复）。
3. **云端零付费，账单恒为 $0.00。** 禁止 R2 的 `InfrequentAccess` 存储类；
   禁止「整包下载来判断存在」的高频轮询。

---

## 6. 这个项目最容易犯的错（**都是实测过的，不是假设**）

1. **判据绿了但指错了文件。** 已发生二十七次以上。
   改完判据要**真去把它该抓的东西改坏一次**，看它红不红；**正例必须同时是绿的**。
2. **空默认值吞掉「不知道」。** `[]` / `{}` / `0 个文件` 都会被读成「没问题」。
   判据里凡有早退分支，**返回的字段形状必须和正常分支一样**，只多一个「未核验」标记。
3. **自述不是证据。** 子代理说「我没读 holdout」不算数，要有独立通道去核。
4. **夹具比真东西干净就等于没测。** 自测夹具要像真语料一样脏（OCR 讹字、跨行连字符、页眉插进词中间）。
5. **逐字引文就是逐字。** OCR 讹字**不许改**；要给还原读法就写在括号里并注明「这是判读」。
6. **报数之前先跑一遍命令。** 手写的数必然往好里漂。
7. **没做完不能停。** 发现意外先把不依赖它的事做完，别用汇报替代推进。
8. **达不到门时不要放宽判据。** 选诚实退路（记延后 / 记拒发）+ 写台账，继续往下走。
   ★ **尤其是这条门正挡着你的时候。** 2026-08-10 实测过一次：
   `status: hypothesis` 被门当成 `pattern` 要 ≥2 处来源，
   而全库爆炸半径是 **2 条（都是我当轮刚写的）**——**改它安全，但不正当**，
   所以改了产物不改门，把问题记成待裁定 ㉝。
9. **★ 不是所有真缺陷都有判据形状的探测器。** 同一天两次：
   - 「某句是不是译者的编者话」——窗口共现上**事故句 60% ＞ 真段落 56%，顺序是反的**；
   - 「这份语料根本不是他的」——三把尺子（姓零命中 290 份 / P 档零命中 242 份 /
     文件名实词不在正文 86 份）**全被合理情形淹没**
     （Godin 的博客正文只写 `Seth's Blog` 不带姓，196/196 全零）。

   **两次都是靠「先缩到异常组，再读原文」查出来的**，不是靠全库扫。
   查不出来就**如实写「这一条没有判据兜底」**，别上线一个抓不到本案的判据。
10. **★ 比相似度之前先做负对照。** `difflib` 的 `quick_ratio` **只比字符多重集**：
    两本毫不相干的书给 **0.945**（真 ratio 0.012）。
    换 8 词片 Jaccard 也踩过一次——**按固定步长取片会因错位让逐字相同的两份得 0.000**，
    要按 `zlib.crc32(片) % k == 0` 取样（内建 `hash()` 带每进程随机种子，不能用）。
    **同一件事上量错三次，每次都是负对照或读命中挡回来的。**

---

## 7. 交接时的注意

### ★★★★ 给用户的一句话 prompt（**合并到 main 之后才成立**）

```
接手我的人物蒸馏项目：cd ~/Documents/Codex/GithubProject/AgentDatabase && git pull，读 HANDOFF.md 按它继续做，遇到标「待裁定」的条目停下来问我。
```

**不需要任何设置**：路径是本机已有的主树，`git pull` 之后 `HANDOFF.md` 就在仓根。

### ★★★★ 它现在还不成立，缺的是这一步

实测（2026-08-10）：

| 检查 | 结果 |
|---|---|
| `~/Documents/Codex/GithubProject/AgentDatabase/HANDOFF.md` | **不存在** |
| 主树分支 / 状态 | `main` / 干净 |
| 主树 HEAD vs 本分支 | **落后 1027 个提交**（2026-08-11 当场跑；★ 每提交一次就变） |

**HANDOFF.md 只在 `claude/character-distillation-skill-reorganize-d57595` 上。**
移交那晚要做完的是：

```bash
git push -u origin claude/character-distillation-skill-reorganize-d57595
gh pr create --fill && gh pr merge --squash --delete-branch
cd ~/Documents/Codex/GithubProject/AgentDatabase && git pull
```

做完之后，上面那句 prompt 才会在收件人的布局里跑通。

### ★★ 这一推有多大（实测，2026-08-10）

| 项 | 值 |
|---|---|
| 待推送提交 | **1027**（2026-08-11 实测；★ 每提交一次就变，**要报就当场跑** `git rev-list --count origin/main..HEAD`） |
| 仓内 pack | **835.94 MiB** |
| 已跟踪的语料文件 | **9,578** |
| **最大的单个已跟踪文件** | **18.1 MB**（`probe-adams-131/raw/whoswho1922_djvu.txt`） |

★ **没有文件超过 GitHub 的 100 MB 硬上限**，所以不会因为单文件被整推拒掉。

★★★★ **`git push --dry-run` 2026-08-10 实跑通过**（联了服务器，只是不更新 ref）：

```
To github.com:LinzeColin/AgentDatabase.git
 * [new branch]  claude/character-distillation-skill-reorganize-d57595 -> ...
```

**远端可达、凭据可用、分支会作为新分支建立、无任何拒绝。**
移交那晚照 §7 的三条命令走即可。
★★ 但这是一次**大推**（语料整个在库里），网络慢的时候会跑很久——
**移交那晚给它留时间，别掐掉。**
★★★ `git count-objects` 会报两条 `garbage found: …/worktrees/agentdb-nasmyth-153/info/sparse-checkout`
的警告——那是 worktree 的元数据，**与推送无关，不要去动它**。

### 已经在**干净检出**里验过的（不是在我的工作目录里验的）

`git worktree add --detach` 一个全新检出，逐条跑：

| 步骤 | 结果 |
|---|---|
| `HANDOFF.md` 在仓根 | ✓ |
| §2 那条「当场跑一遍」的产物计数命令 | ✓ 101 |
| `_ledgers/_每次开工必读.md` | ✓ |
| `references/pipeline/next_person.py` | ✓ **NEXT = William Paton（财务合规师）** |

★★★★ **但那次演练只验了这 4 条，§3 的命令表一条都没跑过**——
于是 `namesake_gate.py <人名>`（真实签名是 `--name`）活到了 2026-08-11，
**接手方照抄的第一条命令就会报错**。
现在 `check_handoff_commands.py` 把这一类管起来了（已接进 `finalize_release.py`）：
它跑每条命令的 `--help` 取真实签名，比对必填 flag / 位置参数 / 互斥必选组 / 子命令。
★ 教训是通用的：**「在干净检出里验过」要说清验的是哪几条**，
没说清就等于把「没验的部分」也算进了「验过」。

★ `next_person.py` 会在 stderr 上打印台账来源；两处不一致时它**明说用的是仓内那份**
并给出两边的 sha256 与 mtime。**看到那条警告不是出错，是它在告诉你用了哪一份。**
★★ 演练检出跑完**已经收掉**（铁律 3：谁开的谁收）。

### ★★★★ 教训库：**它原本不在仓里，接手方一条都读不到**

`_ledgers/_教训库/` 是 2026-08-10 移交前才复制进来的 **101 条实测教训**（约 468 KB）。
**原本存在上一任 agent 的私有存储 `~/.claude/projects/…/memory/` 下——
不在 GitHub 上。** 核对移交时才发现这个缺口。

- **入口是 `_索引.md`**：一行一条，带一句话钩子。
- **动手改判据之前先在索引里搜相关的词**——这个项目里判据第一版出错是常态，多半有人踩过。
- ★ **这是快照，不是活文档。** 里面提到的文件、字段、命令可能已经变了，
  引用到具体路径时**先去仓里确认它还在**。
- ★★ **移交那晚要重导一次**（本会话之后又攒了新的）：

  ```bash
  cp ~/.claude/projects/-Users-linzezhang-Documents-Codex-GithubProject-AgentDatabase/memory/*.md \
     CodexSkills/skill_log_evals/persona-distiller/_ledgers/_教训库/
  mv CodexSkills/skill_log_evals/persona-distiller/_ledgers/_教训库/MEMORY.md \
     CodexSkills/skill_log_evals/persona-distiller/_ledgers/_教训库/_索引.md
  ```

### 交接前还要做的

1. ★★★★ **唯一真正的卡点：推 + 合并到 main。** 这一步**必须由用户授权**，
   我不会自己按下去——它是对外可见且不易撤回的。
   - 实测（2026-08-10，**不改变任何远端状态**）：`git push --dry-run` 通过，
     远端可达、分支会**新建**（`* [new branch]`），无拒绝；
     本分支领先 `origin/main` **1027 个提交**（2026-08-11 实测），包 **835.94 MiB**，最大被跟踪文件 18.1 MB（无超 100MB 的）。
   - **合并之前那句一句话 prompt 不成立**——主树上没有 `HANDOFF.md`。
2. **`_scratch/agentdb-nasmyth-153` 这个 worktree 是我开的，得我收**：
   合并 → 关 PR → `git worktree remove` → 删分支 → `git gc`（**禁止 `--prune=now`**）。
3. **`_protected/` 永不上传**，交接时也不上传。
4. **Notion 全程没碰过**，按约定要等 600 人全完成。
5. **教训库同步到 113 份**（`_ledgers/_教训库/`）——★ 它原本不在 GitHub 上，
   接手方一条都读不到。交接当晚**再同步一次**（我每天都在往里写）。
