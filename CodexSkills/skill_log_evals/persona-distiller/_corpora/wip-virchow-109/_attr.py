#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#109 Virchow：attribution_basis + 逐份挂 attribution。

**逐份点名，不用整批声明**——v0.0.0.24 曾因一条整批声明把逐源检查整个关掉，
绿了整整十版；v0.0.0.34 才堵上。
"""
import json
import pathlib
import re

WS = pathlib.Path("workspaces/rudolf-virchow/rudolf-virchow")
LED = WS / "evidence/source-ledger.jsonl"
rows = [json.loads(l) for l in LED.read_text(encoding="utf-8").splitlines() if l.strip()]


def attr(name: str, title: str, year: str) -> str:
    n = (name or "").lower()
    if n.startswith("art-"):
        return ("**从《Archiv für pathologische Anatomie und Physiologie》卷内按署名切出的单篇**。"
                "该刊由他 1847 年创办并长期主编，卷内为多人合著——"
                "**故卷次本身一律记 U，不记 P1**；他本人的文章按正文署名 "
                "「Von R. Virchow」／「Von Rud. Virchow」定位，切至下一位作者的署名为止。"
                "每份文件头记着母卷与字符偏移，**切得对不对可以回卷复核**。")
    if "cellularpath" in n or "cellpath" in n:
        return ("《Die Cellularpathologie in ihrer Begründung auf physiologische und "
                "pathologische Gewebelehre》(Berlin: Hirschwald, 1858)，署 Rudolf Virchow。"
                "**本工作区握有 Deutsches Textarchiv 的双录入转写本**（非 OCR），"
                "与扫本可逐句互核——这是本人物语料里最可靠的一份。")
    if "gesabh" in n:
        return ("《Gesammelte Abhandlungen》系列，**生前自选自编**，署 Rudolf Virchow。"
                "其中 `gesabh-oeffmed-1879-*` 收录了他 1848–49 年《Die medicinische Reform》"
                "周刊的内容——**该周刊原刊本工作区未取得**，此为他本人 1879 年的重印本，"
                "**性质是自选重印，不是他人转录**。")
    if "typhus" in n or "oberschlesien" in n or "hungertyphus" in n:
        return ("1848 年上西里西亚斑疹伤寒调查报告，署 Rudolf Virchow，"
                "系普鲁士政府委派调查后提交的正式报告。")
    if "geschwuelste" in n:
        return "《Die krankhaften Geschwülste》(3 卷, 1863–67)，署 Rudolf Virchow。"
    return ("其生前发表之著作、论文、演讲或报告，署 Rudolf Virchow，发表年在 1845–1902 之间。"
            "**同姓排除三条**：archive.org creator 字段对父作 `Virchow, Rudolf, 1821-1902`、"
            "对子作 `Virchow, Hans, 1852-1940`；**1880 年前之作必非子**（子 1852 年生）；"
            "解剖学教科书与形态学专论属子，病理组织学／细胞病理／公共卫生调查／议会演说属父。")


n = 0
out = []
for r in rows:
    if r.get("tier") == "P1" and not r.get("attribution"):
        r["attribution"] = attr(r.get("original_name") or pathlib.Path(r["local_path"]).name,
                                r.get("title", ""), str(r.get("published_at", "")))
        n += 1
    out.append(r)
LED.write_text("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in out) + "\n",
               encoding="utf-8")

p1 = [r for r in out if r.get("tier") == "P1"]
covered = [{"source_id": r["source_id"],
            "original_name": r.get("original_name") or pathlib.Path(r["local_path"]).name,
            "locator": r.get("locator", "")[:200]} for r in p1]

m = json.loads((WS / "meta.json").read_text(encoding="utf-8"))
m["attribution_basis"] = {
 "authority": (
   "印刷时代人物，署名证据充分。四处须写明：\n"
   "① **核心著作有非 OCR 的双录入转写本**：《Die Cellularpathologie》(1858) 在 "
   "Deutsches Textarchiv 有双录入转写，与扫本可逐句互核。**这比任何 OCR 都可靠**，"
   "逐字引文优先取它。\n"
   "② **他创办并主编的期刊，卷次本身不算他的著作**。"
   "《Archiv für pathologische Anatomie und Physiologie》(1847 起) 卷内多人合著，"
   "**44 个卷次一律记 U**；他本人的文章按正文署名「Von R. Virchow」切出，成 22 个 "
   "`art-*` 单元记 P1，每份记母卷与字符偏移可回卷复核。\n"
   "③ **他用德文写作，本工作区有 30 份译本（英/法）**。"
   "译本是**译者的字**，一律记 P2，**逐字引文只能取德文 P1**。"
   "（Pasteur #106 因外语引文形态未被判据覆盖出过事，v0.0.0.37 才补上。）\n"
   "④ **17 份 Fraktur OCR 已毁的扫本保留在库、一律不记 P1**。"
   "文件不删——删了就没人知道那份扫本坏过；"
   "`check_ocr_language_death --ledger` 硬拦「已毁的被记作 P1」。"),
 "citation": ("Virchow, Rudolf. *Die Cellularpathologie in ihrer Begründung auf "
   "physiologische und pathologische Gewebelehre*. Berlin: Hirschwald, 1858"
   "（并用 Deutsches Textarchiv 双录入转写本互核）。"
   "并对照：*Archiv für pathologische Anatomie und Physiologie* 各卷内其署名文章；"
   "*Gesammelte Abhandlungen zur wissenschaftlichen Medicin* (1856)；"
   "*Die krankhaften Geschwülste* (1863–67)；"
   "1848 年上西里西亚斑疹伤寒报告。"),
 "disputed_policy": (
   "**争议著作为空，但不是「没查过」。** 他身处德国医学期刊的公开发表制度下，"
   "论文有卷期与年份可查，不存在伪托问题。\n"
   "**本人物真正的归属风险是血亲同名，而且危险的那个是他儿子：**\n"
   "**Hans Virchow（1852–1940）**，柏林大学**解剖学**教授，与父同姓、领域紧邻、"
   "著作年代重叠（1880s–1930s）。另有 **Karl Virchow**（另一子，医师）。\n"
   "抓源阶段已据三条机器可复核的判法排除 Hans 的 3 条与 Karl 的 1 条。\n"
   "**★ 一处必须写明的例外**：《Archiv》Bd. 64 (1875) 内有一篇 "
   "「Beobachtungen am Hühnerei über das dritte Keimblatt…, Von Hans Virchow, "
   "Cand. med. in Berlin」——**父主编的刊物上登了子的文章**。"
   "它单列在 `raw/_EXCLUDED.txt` 里，**没有归入任何类别**，"
   "因为它既不是父的著作，也不是「排除掉的子的著作」——它是父刊登子。\n"
   "另有 **《Virchows Archiv》**（1847 起以他命名、沿用至今）造成的刊名淹没："
   "实测该刊 Bd. I 里 `Virchow` 命中约 90 处，其中约 2 处是他本人。"
   "**全文搜 `Virchow` 不可用，须按 creator 字段取。**"),
 "disputed_works": [],
 "exclusions": [
   {"what": "其子 Hans Virchow（1852–1940）的著作",
    "why": "同姓且领域紧邻；判法：creator 字段 / 1880 年前必非子 / 解剖学与形态学属子",
    "excluded_ids": ["b22288338", "derdottersackdes00virc", "ueberbauundnerva00virc"]},
   {"what": "另一子 Karl Virchow 的著作", "why": "同姓；同法排除",
    "excluded_ids": ["analytischemeth00vircgoog"]},
   {"what": "《Archiv》各卷内他人所撰文章",
    "why": "他是主编不是唯一作者；卷次记 U，其本人文章另切为 art-* 记 P1"},
   {"what": "英译本与法译本（30 份）",
    "why": "**译者的字，不是他的字**；记 P2，逐字引文不得取"},
   {"what": "《Archiv》Bd. 64 (1875) 内 Hans Virchow 署名的一篇",
    "why": "**父主编的刊物上登了子的文章**——单列不归类，见 raw/_EXCLUDED.txt"},
   {"what": "17 份 Fraktur OCR 已毁的扫本",
    "why": "文本读不出字，逐字引文不可取；**保留在库不删**，一律不记 P1"}],
 "counting_convention": (
   f"covered_sources 逐份点名全部 {len(p1)} 条 P1 源，不使用整批声明"
   "（v0.0.0.24 曾因整批声明导致逐源检查整个关闭，v0.0.0.34 已堵）。\n"
   "**注意**：75 条 P1 含 22 个从期刊卷内切出的 `art-*` 单篇与若干同文异扫，"
   "**算独立著作数时不得重复计**。"),
 "covered_sources": covered,
}
(WS / "meta.json").write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"attribution 逐条挂 {n} 条；covered_sources 点名 {len(covered)} 条")
