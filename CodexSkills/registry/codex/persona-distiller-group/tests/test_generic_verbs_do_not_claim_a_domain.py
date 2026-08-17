#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**通用动词不能单独把一个域拉进来** —— `设计` / `design` 那一次。

## 抓到它的那一次（2026-08-17）

`test_new_operator_deliveries_are_available_to_routing` 红着。追到中文那道
零售扩张题：`Anne Mulcahy` 排 **第 38 / 70**，而 John Maeda（艺术设计师）
与 Seth Godin（客户营销师）排 **第 1、第 2**。

    题：为零售企业**设计**低价、库存周转、门店集群、物流密度、供应链…的扩张战略
    分到的域：['operations-product', **'creative-design'**]

`domain_match = |族的域 ∩ 题的域| / |题的域|`，而域集恰好是
`{creative-design, operations-product}` 的两族（艺术设计师／客户营销师）
拿满分 **1.000**，真正对口的创业经营师只有 **0.500**。

成因是一个词：**`设计` 与 `design` 在两种语言里主要都是动词**
（设计战略／设计实验／"design an experiment"／"type design"），
而它们是 `creative-design` 的裸关键词，命中一个就收下整个域。

    「…**设计**…扩张战略」        → 含 creative-design
    把「设计」换成「制定」          → **不含**（受控对照）
    英文软件题（"Design a"/"type design"）→ 含 creative-design
    "system design interview"    → **纯** creative-design（一道软件题）

处置：把这两个词降为**弱信号** —— 只有同域另有强词命中时才计数
（`WEAK_SIGNALS`，见 `compile_task_graph.py`）。
★ 只降这两个，且都是**实测误发过的**；不凭感觉扩名单。
"""
import pathlib
import subprocess
import sys
import unittest

_r = subprocess.run(["git", "-C", str(pathlib.Path(__file__).resolve().parent),
                     "rev-parse", "--show-toplevel"], capture_output=True, text=True)
REPO = pathlib.Path(_r.stdout.strip()) if _r.returncode == 0 else pathlib.Path(".").resolve()
sys.path.insert(0, str(REPO / "CodexSkills/registry/codex/persona-distiller-group/scripts"))


class GenericVerbsDoNotClaimADomain(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from compile_task_graph import infer_domains
        cls.dom = staticmethod(infer_domains)   # ★ 普通函数挂类上会变绑定方法

    # ── 误报侧：这些**不该**被判成 creative-design ──
    def test_chinese_strategy_task_is_not_creative_design(self):
        d = self.dom('为零售企业设计低价、库存周转、门店集群、物流密度、供应链和一线客户反馈的扩张战略')
        self.assertNotIn("creative-design", d)
        self.assertIn("operations-product", d)

    def test_english_software_task_is_not_creative_design(self):
        d = self.dom('Design a software engineering review covering TDD, refactoring, '
                     'distributed systems API type design and technical teaching')
        self.assertNotIn("creative-design", d)
        self.assertIn("software-ai", d)

    def test_design_an_experiment_is_not_creative_design(self):
        self.assertNotIn("creative-design", self.dom('design an experiment to measure latency'))

    def test_bare_verb_alone_claims_nothing(self):
        """★★ 只有通用动词、没有任何强词 ⇒ 不许认领 creative-design。

        代价说明白：这也意味着「做一个设计」这种只有通用词的题会落到
        `general-decision`（路由会如实披露无信号）。**这是收紧侧的已知代价。**
        """
        self.assertNotIn("creative-design", self.dom('做一个设计'))
        self.assertNotIn("creative-design", self.dom('system design interview about sharding'))

    # ── ★ 负对照：真·设计题必须照旧命中，否则就是把信号修没了 ──
    def test_real_design_tasks_still_hit(self):
        for t in ('为一本诗集做版式与字体设计',
                  'typography and palette for a poetry anthology',
                  '品牌视觉设计与配色规范',
                  'UI 与 UX 设计评审'):
            with self.subTest(task=t):
                self.assertIn("creative-design", self.dom(t), t)

    def test_weak_plus_strong_counts_more_than_strong_alone(self):
        """★ 弱信号在有强词时**要计数**（否则等于把它删了）。"""
        from compile_task_graph import infer_domains, DOMAIN_SIGNALS, WEAK_SIGNALS
        self.assertIn("设计", WEAK_SIGNALS["creative-design"])
        self.assertIn("design", WEAK_SIGNALS["creative-design"])
        # 两者都在词表里，才谈得上「降为弱」而不是「删掉」
        for w in WEAK_SIGNALS["creative-design"]:
            self.assertIn(w, DOMAIN_SIGNALS["creative-design"])


class HomonymKeywordsDoNotCrossFire(unittest.TestCase):
    """**同音异义**：`仓库` 在词表里指 git 仓库，而中文里它也是 warehouse。

    实测（2026-08-17）：基准题 `warehouse-automation-roi`
    「仓库要不要上自动分拣，投入 800 万，三年能不能回本？」
    —— 相关族是建造采购师/投资资本师/创业经营师，**没有软件开发师** ——
    被判成软件题，域从 2 个变 3 个，domain_match 分母变大、人人被稀释。
    该题正是基准里最差的几道之一（−11.5%）。

    证据够不够动手：`仓库` 在 24 道题里**只命中这一道**，去掉后该题
    software-ai 命中归 0 ⇒ **没有任何真软件题靠它**。改后该题 **−11.5% → −8.9%**，
    24 题里**没有任何一题变差**。
    """

    @classmethod
    def setUpClass(cls):
        from compile_task_graph import infer_domains
        cls.dom = staticmethod(infer_domains)

    def test_warehouse_question_is_not_software(self):
        d = self.dom("仓库要不要上自动分拣，投入 800 万，三年能不能回本？")
        self.assertNotIn("software-ai", d)
        self.assertIn("engineering-industry", d)
        self.assertIn("finance-investment", d)

    def test_code_repository_still_hits_software(self):
        """★ 负对照：git 那个意思**必须照旧命中**，否则就是把信号删了。"""
        for t in ("代码仓库的分支策略怎么定", "repo 的 branch protection 怎么配",
                  "monorepo repository layout review"):
            with self.subTest(task=t):
                self.assertIn("software-ai", self.dom(t), t)

    def test_bare_warehouse_word_is_gone_from_the_list(self):
        """★★ 钉住：裸 `仓库` 不许再回到 software-ai 词表里。"""
        from compile_task_graph import DOMAIN_SIGNALS
        self.assertNotIn("仓库", DOMAIN_SIGNALS["software-ai"])
        self.assertIn("代码仓库", DOMAIN_SIGNALS["software-ai"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
