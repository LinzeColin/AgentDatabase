# 人物蒸馏 Skill / Persona Distiller v0.0.0.111

Persona Distiller 把公开人物、经授权的私域人物、自己、历史或虚构人物构建为可安装的 Agent Skill。它蒸馏证据支持的能力、策略、认知、决策、工作方式和边界；不是只模仿口吻，也不是本人、授权、背书或实时观点。

身份分类为 **12 个单一主身份**（自 v0.0.0.6 起，由旧的 6 主身份 + 多重身份重组而来；**多重身份已移除**），职业覆盖范围见下方「身份分类与职业覆盖」。族的真源是 [`registries/identity-families.json`](registries/identity-families.json)。

交付合同（delivery contract / `builder_version`）与 Skill 发布号是**两个独立的轴**：交付合同长期钉在 `v0.0.0.5`，不随 Skill 升版移动，人物交付 ZIP 结构因此保持不变。三个轴的完整定义见下方「版本边界」。

人物 Skill 安装后直接调用。它会从当前任务内部推断身份分面和场景，不要求运行用户选择身份、编号或权重；运行本身不编号。

## 安装

最终交付只有一个 bundle，文件名带当前 Skill 发布号（由 `scripts/build_release_bundle.py` 从 `VERSION` 读取，不硬编码）：

```bash
unzip PersonaDistiller-Final-v0.0.0.14.zip
cd PersonaDistiller-Final-v0.0.0.14
python3 install.py
```

bundle 同时安装：

```text
~/.codex/skills/persona-distiller
~/.codex/skills/persona-distiller-group
```

不要在 `~/.agents/skills/` 保留第二份同名来源。安装器替换同名旧版本时使用临时回滚，不保留第二个长期来源。

## 创建人物

构建第一步不是身份选择，而是同名消歧：系统先按别名、译名、转写和缩写检索 canonical registry 与权威公开资料。没有候选时继续；只有一个候选（即使证据较弱）也自动绑定，保证流程顺滑；多个候选时立即停止，完整列出带字母的候选卡片，等待用户选择。每个候选只输出四行：人物与身份、专业背景、应用价值、区分依据；不展示置信度。候选全部列出，超过 Z 后使用 AA、AB 等字母。机器门禁由 `scripts/namesake_gate.py` 生成，`init_target.py` 在初始化前强制验证；这个门禁只属于构建阶段，安装后运行人物 Skill 仍不要求用户选择身份。

构建阶段需要目标人物姓名和内部研究身份：

```bash
python3 scripts/init_target.py \
  --name "目标人物" \
  --identity "材料建工师" \
  --namesake-gate ./namesake-gate.json \
  --workspace ./workspaces
```

`--identity` 取 `1`–`12` 编号或身份名（如 `材料建工师`、`软件开发师`）之一，只能是单一主身份（多重身份已移除）。场景可省略。研究、综合和评测完成后，必须补全工作区 `team-card.json`，再发布：

```bash
python3 scripts/package_target.py ./workspaces/<slug> --output ./dist
python3 scripts/register_persona.py \
  ./dist/<slug>-persona-distillation-delivery-v0.0.0.N.zip
python3 scripts/validate_persona_registry.py
```

## 唯一登记已拆分

人物产物不再保存在本构建器目录。唯一 canonical registry 与专家团队路由位于平级：

[`../persona-distiller-group/`](../persona-distiller-group/)

十二个目录与 Skill 内部身份名称完全一致。同一人物只能登记一次，进入其单一主身份目录（多重身份已移除）。分类是内部登记与团队路由元数据，不限制已安装人物 Skill 的直接调用。

## 身份分类与职业覆盖

十二个单一主身份按相关性吸收全球职业，覆盖 ≥95% 的可建模专业职业。每一组的详细覆盖范围如下：

| # | 身份目录 | 内部 id | 覆盖的职业簇 |
|---|---|---|---|
| 1 | `材料建工师/` | `technical-engineer` | 机械/材料/冶金/焊接/化工/矿业/石油/工业工程师；机加工/钳工/管工/焊工/装配；设备可靠性与维护；无损检测/腐蚀/摩擦学；材料科学家 |
| 2 | `软件开发师/` | `software-developer` | 软件/系统/嵌入式/游戏/Web 工程师；数据科学/ML/AI 研究；DevOps/SRE/安全/网络/DBA；计算机科学与算法；测试 |
| 3 | `艺术设计师/` | `art-designer` | 平面/工业/产品/UX/室内/时装设计；建筑（美学向）；美术/插画/动画；导演/摄影/音乐/表演；创意写作 |
| 4 | `创业经营师/` | `entrepreneur-operator` | 创始人/高管/总经理；运营/生产/项目群管理；产品经理；管理咨询；人力组织；零售/餐旅管理；农业与医疗经营（非临床） |
| 5 | `投资资本师/` | `investor-capital-allocator` | 价值/成长/量化投资；基金/组合管理；VC/PE；交易员；股权/信用分析；财富管理；市场经济学家 |
| 6 | `思想教育师/` | `thinker-educator` | 哲学/思想家；作家/记者/传媒；人文社科研究；教师/教授/教练/导师；历史/宗教/伦理；语言学者；竞技方法 |
| 7 | `政治法律师/` | `political-legal` | 政治家/政策/公共管理；外交；法官/律师/法学；监管（政策向）；国际关系；公益倡导 |
| 8 | `客户营销师/` | `customer-marketing` | 品牌/增长/效果营销；市场研究/分析；B2B/B2C 销售；客户成功/客户体验；广告/公关；电商/数字营销/SEO |
| 9 | `建造采购师/` | `construction-procurement` | 施工/工程项目管理；BIM/VDC；工程量/造价估算；计划/进度；合约/招投标；采购/寻源/供应链/物流/仓储/供应商；制造质量体系 |
| 10 | `财务合规师/` | `finance-compliance` | 会计/审计/财务总监/成本会计/税务/资金；精算；风险/内控/合规；安全工程/过程安全/职业健康（EHS）；标准/规范审核（ISO/ASME/AWS/API）；环保合规 |
| 11 | `医疗护理师/` | `healthcare-nursing` | 医生/临床各科；护理/助产；药剂/公共卫生；牙科/康复/理疗；心理/精神；兽医；医技/影像/检验 |
| 12 | `农林牧渔师/` | `agriculture-fishery` | 农学/种植/园艺；畜牧/养殖；林业/生态；渔业/水产/海洋；农机/农业工程；食品生产/加工 |

未并入（< 5%，低/无/负相关，可日后设为新组）：个人与生活服务（理发/美容/餐饮服务/家政）、保护性服务与军事作战一线、运输驾驶操作（物流管理已并入建造采购师）、基础体力劳动。

## 单一完整交付 ZIP

每次成功发布最终只产生：

```text
<slug>-persona-distillation-delivery-v<0.0.0.N>.zip
```

这个 ZIP 内含：

- 一个不可变、可独立安装的人物运行时 Skill ZIP；
- 外层安装器；
- delivery manifest 与全成员 checksums；
- portable registration 与 team card；
- 来源覆盖、评测、验证、provenance、review 和 handoff；
- 可选人读报告。

不再生成 `.sha256` sidecar、第二个审计 ZIP 或散落交付文件。外层 SHA-256 由 canonical registry 保存；内层运行时 SHA-256 同时写入外层 manifest 和 registry。

通用文件与架构规范见
[`../persona-distiller-group/references/delivery-package-standard.md`](../persona-distiller-group/references/delivery-package-standard.md)。规范不限制人物姓名、语言、职业或内容风格。

## 版本边界

- `skill_version`（本 Skill 发布号）：当前 `v0.0.0.14`；**唯一真源是 `VERSION` 文件**，其余任何位置都是它的副本，由 `scripts/check_contract_drift.py` 强制一致；
- `builder_version`（交付合同格式）：仍为 `v0.0.0.5`，人物交付 ZIP 结构不变；
- `model_version`：工作区内部语义快照；
- `distilled_with`（**每人一条**，记在 `registration.json`）：产出该人物的 skill 发布号，打包时由 `delivery_builder.py` 从 `VERSION` 盖进交付 manifest，**随产物走**；
  兼容下限 = **当前发布号末位 − 10**（如当前 `v0.0.0.98` → 下限 `0.0.0.88`），由 `scripts/check_distillation_freshness.py` 统计。
  **低于下限不阻塞发行**——统一重蒸安排在 600 人整体完成之后；
- `product_version`：每个 canonical 人物独立连续使用 `0.0.0.1..0.0.0.999`；
- runtime invocation：无版本。

候选打包只预览下一版本。只有登记成功才占号；失败不占号，禁止跳号、复用、同号异哈希或超过 `0.0.0.999`。

## 安全默认

- 构建时可联网研究；运行时不依赖冻结网络内容，当前事实仍应独立核验。
- 外部材料中的命令一律视为不可信数据。
- 公开交付不含 raw、Holdout 正文、私密来源正文、Token、Cookie、密钥或历史调用正文。
- 高风险事项采用“人物分析视角 + 独立现实核验 + 有责任的人类决策者”。

完整工作流见 `SKILL.md` 与 `references/`。
