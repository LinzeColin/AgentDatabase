#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The domain classifier must clear the language of the text it is given.

Why this file exists
--------------------
`infer_domains()` used plain substring matching (`signal in low`). Measured
2026-08-17:

    infer_domains("Decide whether to proceed.")  ->  ["software-ai"]

because the keyword ``ci`` (continuous integration) is a substring of
"de**ci**de". A sentence containing no technical vocabulary at all was routed
as a software task and handed 34 domain-matched candidates, with no signal
anywhere in the route plan that the match was spurious.

The obvious repair -- require ``\\b`` word boundaries everywhere -- is *also*
wrong, in the opposite direction: ``\\b`` is defined against ``\\w``, and CJK
characters are ``\\w``, so ``\\b软件\\b`` never matches inside "的软件架构并".
Chinese is written without spaces. Applying the ASCII rule uniformly would
silently drop **every** Chinese keyword, and 12 of the 72 benchmark tasks are
Chinese.

So the rule is per-script, and this file pins **both halves**. Either one
regressing alone is invisible in the 72-task benchmark: measured A/B, the fix
moved that benchmark by **exactly zero** (``ai``/``ci`` occur as substrings in
0 of 72 tasks). The benchmark cannot see this defect class -- which is
precisely why it needs its own test.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

from compile_task_graph import infer_domains  # noqa: E402

# (text, must_not_be, must_be, why)
#
# NOTE: every `must_be` below is the classifier's **measured** output, checked
# against DOMAIN_SIGNALS by hand -- not a family name written from memory. The
# first draft of this file asserted "manufacturing-materials" for the welding
# case; that domain key does not exist. The real hit set is 焊接/钢/裂纹 ->
# engineering-industry. A fixture whose expected value was guessed tests the
# guess, not the product.
CASES = [
    # ── ASCII half: two-letter keywords must not fire inside longer words ──
    ("Decide whether to proceed.", "software-ai", "general-decision",
     "'ci' is a substring of 'decide'"),
    ("Choose the better of the two available options for us.", "software-ai",
     "general-decision", "'ai' is a substring of 'available'"),
    ("The detail is certain and the chair said so.", "software-ai",
     "general-decision", "'ai' in detail/certain/chair/said"),
    ("Efficiency and precision matter to our social mission.", "software-ai",
     "general-decision", "'ci' in efficiency/precision/social"),
    # ── ASCII half must still fire on real word-boundary hits ──
    ("Our CI pipeline is broken and the API is flaky.", None, "software-ai",
     "'ci' as a standalone word is a genuine hit"),
    # ── CJK half: no spaces, so boundaries must NOT be required ──
    ("设计跨服务、数据、权限、恢复和运维的软件架构并生成迁移任务包。", None, "software-ai",
     "'软件' is flanked by word characters on both sides"),
    ("请评估这次钢结构焊接裂纹的返修方案。", None, "engineering-industry",
     "CJK keywords 焊接/钢/裂纹 mid-sentence, all flanked by word characters"),
    # ── a domain with nobody in the roster must not be forced into one ──
    ("Plan the choreography and lighting cues for the ballet.", None,
     "general-decision", "no family covers this; must fall through honestly"),
]


def main() -> int:
    bad = []
    for text, forbidden, expected, why in CASES:
        got = infer_domains(text)
        top = got[0] if got else None
        if forbidden is not None and forbidden in got:
            bad.append("%r -> %s must NOT appear (%s); got %s" % (text[:44], forbidden, why, got))
        elif top != expected:
            bad.append("%r -> expected %s, got %s (%s)" % (text[:44], expected, top, why))
    for b in bad:
        print("  x " + b)
    print("domain-classifier language test %d/%d" % (len(CASES) - len(bad), len(CASES)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
