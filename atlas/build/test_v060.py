#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v0.6.0 的负控。**每一条都对应一个「不做这条就会产生假数据」的失败形态。**

负控自身也要能红：删掉被测的那段逻辑，这里必须挂。
不这样的话，一组永远绿的测试只是在给假数据背书。
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build as B          # noqa: E402
import outward             # noqa: E402
import pricing             # noqa: E402
from recall import Index   # noqa: E402


class Pricing(unittest.TestCase):
    def test_cache_only_session_costs_more_than_zero(self):
        """只有 cache_read、没有 fresh input 的会话，成本必须 >0。

        旧口径 cost = tok_in + tok_out 对这种会话给 0 —— 而 cache_read
        占本机成本的 79.8%。这条挂了就说明成本口径又退回去了。
        """
        s = {"source": "claude-code", "tok_in": 0, "tok_out": 0,
             "tok_cache_r": 1_000_000, "tok_cache_w": 0}
        self.assertEqual(s["tok_in"] + s["tok_out"], 0)      # 旧口径确实是 0
        self.assertGreater(pricing.bie(s), 0)                # 新口径必须 >0

    def test_unknown_provider_is_none_not_zero(self):
        """表里没有的 provider 必须返回 None。

        None 是「不知道」，0 是「没花钱」—— 把 None 当 0 加进总量，
        总量就永远显得是对的。v0.5.x 那批假数字全是这个形态。
        """
        self.assertIsNone(pricing.bie({"source": "mars", "tok_in": 999}))
        self.assertIsNone(pricing.bie({"source": "dsh", "tok_in": 999}))

    def test_zero_tokens_is_none_not_zero(self):
        self.assertIsNone(pricing.bie({"source": "claude-code", "tok_in": 0}))

    def test_no_cross_provider_multiplier_reuse(self):
        """各家倍数必须真的不同，否则「不许跨家套用」只是一句注释。"""
        self.assertNotEqual(pricing.PRICES["anthropic"]["cache_read"],
                            pricing.PRICES["moonshot"]["cache_read"])

    def test_no_price_and_no_usage_are_two_different_buckets(self):
        """「没有价目表」和「没量到 token」必须分开报。

        混在一起会让「dsh 根本没单价」和「这场 claude-code 没记用量」
        看起来是同一件事 —— 而两者的解法完全不同。
        """
        r = pricing.summarize([{"source": "dsh", "tok_in": 100},        # 没价目表
                               {"source": "claude-code", "tok_in": 0},  # 有价目表但没量到
                               {"source": "claude-code", "tok_in": 100}])
        self.assertEqual(r["no_price"]["sessions"], 1)
        self.assertIn("dsh", r["no_price"]["sources"])
        self.assertEqual(r["no_usage"]["sessions"], 1)
        self.assertIn("claude-code", r["no_usage"]["sources"])


class Spread(unittest.TestCase):
    def _s(self, **kw):
        s = {"start": "2026-01-01T22:00:00Z", "end": "2026-01-03T02:00:00Z",
             "day": "2026-01-01", "span_min": 28 * 60,
             "tok_in": 900, "tok_out": 0, "tok_cache_r": 0, "tok_cache_w": 0}
        s.update(kw)
        s["buckets"] = B.hour_buckets(s)
        return s

    def test_multiday_session_splits_and_sum_is_preserved(self):
        """跨 3 天的会话：三天各拿一部分，且三者之和 = 原值。

        和对不上就说明摊的过程里丢了 token —— 那比不摊更糟。
        """
        s = self._s(hourly={"2026-01-01T22": 300, "2026-01-02T10": 300, "2026-01-03T01": 300})
        r = B.token_spread([s])
        got = {d: v["tok_in"] for d, v in r["by_day"].items()}
        self.assertEqual(len(got), 3)
        self.assertEqual(sum(got.values()), 900)

    def test_single_day_session_does_not_move(self):
        s = self._s(start="2026-01-05T09:00:00Z", end="2026-01-05T10:00:00Z",
                    day="2026-01-05", span_min=60, hourly={"2026-01-05T09": 900})
        self.assertEqual(B.token_spread([s])["moved_share"], 0.0)

    def test_missing_hourly_is_counted_as_guessed(self):
        """没有逐条时间戳的来源必须落进 guessed_share，不能混进「已知」。"""
        self.assertEqual(B.token_spread([self._s()])["guessed_share"], 1.0)

    def test_peak_comparison_is_published_not_swapped(self):
        """新旧对照必须都在。只给新值 = 偷换口径，用户看不出换过。"""
        r = B.token_spread([self._s(hourly={"2026-01-01T22": 100, "2026-01-03T01": 800})])
        for k in ("peak_before", "peak_after", "peak_delta"):
            self.assertIn(k, r)


class Outward(unittest.TestCase):
    SESS = [{"kind": "human", "start": "2026-08-19T10:00:00Z", "title": "t",
             "prompts": ["明天把报价发给甲方"]}]
    GH = {"state": "通", "repos": [{"repo": "A", "private": False}],
          "days": [{"d": "2026-08-19", "releases": 2}]}

    def test_empty_criteria_becomes_unknown_not_zero(self):
        """判据被清空必须变「说不准」，不能变 0。

        变 0 的话，一条坏掉的判据会被读成「确实一次都没有」——
        那是本项目最贵的一类 bug（v0.5.4 的「常见话题 30/30 全空」就是它）。
        """
        saved = {k: v["pat"] for k, v in outward.TEXT_SIGNALS.items()}
        try:
            for k in outward.TEXT_SIGNALS:
                outward.TEXT_SIGNALS[k]["pat"] = ""
            r = outward.build(self.SESS, self.GH, today="2026-08-20")
            soft = [x for x in r["signals"] if x["kind"] in saved]
            self.assertTrue(soft)
            for x in soft:
                self.assertEqual(x["state"], "说不准")
        finally:
            for k, v in saved.items():
                outward.TEXT_SIGNALS[k]["pat"] = v

    def test_no_github_makes_headline_unknown(self):
        r = outward.build(self.SESS, {}, today="2026-08-20")
        self.assertEqual(r["headline"]["state"], "说不准")

    def test_file_paths_and_column_names_do_not_count_as_money_actions(self):
        """路径和表格列名不算「对外动作」。

        第一版实测 30 天命中 41 次，逐条查完全是
        `.../2026年商务部报价群/sheet_0013.jpg` 和 `账龄回款` 这样的东西。
        """
        rx = re.compile(outward.TEXT_SIGNALS["money"]["pat"], re.I)
        for noise in ("~/photo_sheets/2026年商务部报价群/sheet_0013.jpg",
                      "Sheet10 未来回款预测需要加图表",
                      "合同模板（服务/外协/零星采购）",
                      "项目成本页 → 账龄回款"):
            self.assertIsNone(rx.search(outward._clean(noise)), noise)

    def test_real_money_actions_are_caught_in_both_word_orders(self):
        """动词在前在后都要认。只认「发报价」会漏掉「把报价发给甲方」。"""
        rx = re.compile(outward.TEXT_SIGNALS["money"]["pat"], re.I)
        for hit in ("明天把报价发给甲方", "帮我开张发票给他们",
                    "收到回款 32000", "昨天签了合同", "把报价单发过去"):
            self.assertIsNotNone(rx.search(outward._clean(hit)), hit)

    def test_soft_signals_never_enter_the_headline(self):
        """「说过」不许进头条。头条只数机器可核的事实。"""
        r = outward.build(self.SESS, self.GH, today="2026-08-20")
        self.assertEqual(r["headline"]["n_30d"], 2)     # 只有 release 那 2 次


class Recall(unittest.TestCase):
    ROWS = [
        {"line": "禁止 InfrequentAccess 存储类，R2 免费额度只覆盖 Standard",
         "terms": ["禁止", "infrequentaccess", "存储", "储类", "免费", "额度"], "pointers": []},
        {"line": "清缓存用 git gc，禁止 --prune=now",
         "terms": ["清缓", "缓存", "git", "gc", "prune", "禁止"], "pointers": []},
        {"line": "主树只读，开发一律在 worktree",
         "terms": ["主树", "只读", "开发", "一律", "worktree"], "pointers": []},
    ]

    def test_unknown_question_injects_nothing(self):
        """语料里从没出现过的问题必须 0 注入。

        「什么都命中」是这类功能最常见的假绿：注入永远非空，
        看起来一直在工作，实际上从来没帮上忙。
        """
        idx = Index(self.ROWS)
        for q in ("帮我写一首关于蒲公英的十四行诗",
                  "What is the capital of Burkina Faso",
                  "zzzq wubaliq foobarbaz 1928374",
                  "recommend a good italian restaurant nearby"):
            self.assertEqual(idx.search(q), [], q)

    def test_known_question_hits(self):
        idx = Index(self.ROWS)
        self.assertTrue(idx.search("R2 存储类要不要用 InfrequentAccess"))
        self.assertTrue(idx.search("git gc 能不能加 prune"))

    def test_missing_index_returns_empty_and_does_not_raise(self):
        """索引缺席 = 静默成功。一个会让人问不了问题的沉淀系统比没有更糟。"""
        from recall import recall
        self.assertEqual(recall("随便问点什么", "/tmp/atlas-no-such-index.jsonl"), "")

    def test_stopwords_are_not_evidence(self):
        self.assertNotIn("the", __import__("recall").tokens("the quick brown fox"))


class Populations(unittest.TestCase):
    def test_rate_gate_catches_what_density_misses(self):
        """速率闸必须抓到密度抓不到的那一类。

        v0.5.3 的教训：评委面板每条提示词带不同人名、摊在几小时里，
        密度（≥15 场/小时）和形态（无人发言）两条都躲得过去。
        """
        import aei
        # 同一段提示词前缀，一天之内 6 次，但摊在 6 个不同小时里（密度不触发）
        sess = [{"source": "x", "start": f"2026-05-01T0{h}:00:00Z", "kind": "human",
                 "turns": 3, "prompts": ["You are an independent evaluator. Score the following"]}
                for h in range(6)]
        p = aei._populations(sess)
        self.assertEqual(p["counts"]["F"], 0)          # 密度确实没抓到
        self.assertEqual(p["counts"]["B"], 6)          # 速率闸抓到了
        self.assertEqual(p["caught_by"]["速率"], 6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
