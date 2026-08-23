#!/usr/bin/env python3
# 批量探源：艺术设计师族 30 人（T1-1-300 #121-150）
# 目标：判定 IA 是否有足量 pre-1931 PD 一手文字语料（letters/theory/treatise/autobiography）
# 零 LLM，只调 IA 检索。
import subprocess, sys, os, csv, io

PROBE = "CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline/probe_ia.py"
OUTDIR = "CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline/_probe-art"

PEOPLE = {
121:"Rembrandt",122:"Johannes Vermeer",123:"Francisco Goya",124:"Auguste Rodin",
125:"Vincent van Gogh",126:"Paul Cézanne",127:"Claude Monet",128:"Edvard Munch",
129:"Gustav Klimt",130:"Henri Matisse",131:"Marcel Duchamp",132:"Wassily Kandinsky",
133:"Piet Mondrian",134:"Paul Klee",135:"Man Ray",136:"Salvador Dalí",
137:"René Magritte",138:"Georgia O'Keeffe",139:"Jackson Pollock",140:"Andy Warhol",
141:"Barbara Hepworth",142:"Isamu Noguchi",143:"Filippo Brunelleschi",144:"Gian Lorenzo Bernini",
145:"Christopher Wren",146:"Leon Battista Alberti",147:"Andrea Palladio",148:"Louis Sullivan",
149:"Ludwig Mies van der Rohe",150:"Alvar Aalto"}

# 每人 2 查询：(姓名+文字关键词) / (姓名+letters/notes)
QUERIES = {
121: ["Rembrandt letters etchings writings","Rembrandt Harmenszoon"],
122: ["Vermeer letters writings","Johannes Vermeer"],
123: ["Goya letters writings","Francisco Goya"],
124: ["Rodin art conversations letters","Auguste Rodin"],
125: ["van Gogh letters to his brother","Vincent van Gogh writings"],
126: ["Cézanne letters correspondance","Paul Cézanne"],
127: ["Claude Monet letters writings","Monet correspondence"],
128: ["Edvard Munch writings letters","Munch diary notes"],
129: ["Gustav Klimt letters writings","Klimt correspondence"],
130: ["Henri Matisse notes of a painter","Matisse writings letters"],
131: ["Marcel Duchamp writings","Duchamp notes letters"],
132: ["Kandinsky concerning spiritual in art","Wassily Kandinsky point line plane"],
133: ["Piet Mondrian neo plasticism writings","Mondrian theory plastic"],
134: ["Paul Klee pedagogical sketchbook","Klee diaries writings"],
135: ["Man Ray self portrait writings","Man Ray photographs writings"],
136: ["Salvador Dali secret life","Dali writings"],
137: ["Rene Magritte writings letters","Magritte surrealism writings"],
138: ["Georgia O'Keeffe letters writings","O'Keeffe autobiography"],
139: ["Jackson Pollock writings interviews","Pollock letters"],
140: ["Andy Warhol writings philosophy","Warhol interviews"],
141: ["Barbara Hepworth writings","Hepworth sculpture letters"],
142: ["Isamu Noguchi writings","Noguchi autobiography sculpture"],
143: ["Brunelleschi writings architecture","Filippo Brunelleschi"],
144: ["Bernini letters writings","Gian Lorenzo Bernini"],
145: ["Christopher Wren Parentalia","Wren architecture letters"],
146: ["Alberti de re aedificatoria","Leon Battista Alberti architecture"],
147: ["Palladio four books architecture","Andrea Palladio"],
148: ["Louis Sullivan kindergarten chats","Sullivan autobiography idea"],
149: ["Mies van der Rohe writings","Mies van der Rohe architecture"],
150: ["Alvar Aalto writings architecture","Alvar Aalto"],
}

os.makedirs(OUTDIR, exist_ok=True)
summary = []
for no, name in sorted(PEOPLE.items()):
    seen = set()
    rows = []
    for qi, q in enumerate(QUERIES[no]):
        out = f"{OUTDIR}/{no}.q{qi}.tsv"
        r = subprocess.run(["python3", PROBE, "--query", q, "--rows", "100", "--out", out],
                           capture_output=True, text=True)
        got = []
        if os.path.exists(out):
            with open(out, encoding="utf-8") as f:
                # 跳过 # 注释行，定位真表头（identifier 开头）
                lines = f.readlines()
            hdr_i = next((i for i, ln in enumerate(lines)
                          if ln.startswith("identifier\t")), None)
            if hdr_i is not None:
                body = lines[hdr_i:]
                rd = csv.DictReader(body, delimiter="\t")
                for row in rd:
                    t = (row.get("title") or "").strip()
                    if not t: continue
                    key = t.lower()[:60]
                    if key in seen: continue
                    seen.add(key)
                    got.append((row.get("year") or row.get("date") or "?",
                                row.get("creator") or "", t[:80]))
        # 打印本次命中概览
        numfound = ""
        for line in r.stdout.splitlines():
            if "numFound" in line or "零命中" in line:
                numfound = line.strip(); break
        print(f"#{no} {name} | q{qi}: {numfound} | distinct_titles_sampled={len(got)}")
        for y, c, t in got[:15]:
            print(f"    {y} | {c[:25]} | {t}")
        rows.extend(got)
    # distinct 独立作品粗判：取独特 title 数
    summary.append((no, name, len(set(x[2].lower()[:50] for x in rows))))

print("\n===== 粗判 distinct 汇总（独立标题去重数，需人工复核语义）=====")
for no, name, d in summary:
    print(f"#{no} {name}: ~{d} distinct titles")
