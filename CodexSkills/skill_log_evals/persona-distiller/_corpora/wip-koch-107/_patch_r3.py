#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第 3 轮（最后一轮）：把第 2 轮自己立下却不守的规矩执行到底。

第 2 轮 delta 从 +0.0708 掉到 +0.0562，**是候选自己变差了**：
我加了「引哪一处就说明出自全集还是原刊」，然后在八到十处德文引文里只标了一处。
**加一条自己不执行的纪律，比不提那条纪律更糟。**
"""
import pathlib, re

p = pathlib.Path('gen_rk_answers.py')
t = p.read_text(encoding='utf-8')

# ── ① 逐处给德文引文标版本 ──────────────────────────────────────────
SUB = [
 # trajectory-01：分离与单独接种 —— 原刊
 ('"> «**Um zu erkennen, ob die Bacillen und nicht irgend welche anderen Bestandtheile des "\n'
  '"Milzbrandblutes den Milzbrand erzeugen, müssen die Bacillen aus dem Blute isolirt und "\n'
  '"allein verimpft werden.**»\\n\\n"',
  '"> «**Um zu erkennen, ob die Bacillen und nicht irgend welche anderen Bestandtheile des "\n'
  '"Milzbrandblutes den Milzbrand erzeugen, müssen die Bacillen aus dem Blute isolirt und "\n'
  '"allein verimpft werden.**»\\n"\n'
  '"（**出自原刊**，1884 年结核那本；注意 `isolirt`、`Bestandtheile` 是旧式拼写。）\\n\\n"'),
 # tool-use-01：纯培养与固体面 —— 原刊
 ('"原文：«Die Isolirung der Bacillen lässt sich durch fortgesetzte **Reinkulturen** am "\n'
  '"sichersten erreichen. Es wird zu diesem Zwecke eine geringe Menge von bacillenhaltigem Blut "\n'
  '"auf einen **festen Nährboden** gebracht, auf welchem die Bacillen zu wachsen vermögen.»\\n\\n"',
  '"原文（**出自原刊**）：«Die **Isolirung** der Bacillen lässt sich durch fortgesetzte "\n'
  '"**Reinkulturen** am sichersten erreichen. Es wird zu diesem Zwecke eine geringe Menge von "\n'
  '"bacillenhaltigem Blut auf einen **festen Nährboden** gebracht, auf welchem die Bacillen zu "\n'
  '"wachsen vermögen, **z. B. auf Nährgelatine oder auf gekochte Kartoffeln**.»\\n\\n"\n'
  '"**这一句里同时有旧式的 `Isolirung` 和新式的 `Reinkulturen`——那不是我拼接的，原刊本身就这样。**\\n"\n'
  '"十九世纪末德语正字法正在变，同一位排字工在相邻两句里用两种拼法是常事。"\n'
  '"**所以「照原样」的意思是：连它自己的不一致也一并照抄。**\\n\\n"'),
 # fact-preservation-01：明胶 —— 出自全集
 ('"原文：«Das geeignetste Mittel, um dies zu erreichen, ist ein Zusatz von **Gelatine** zur "\n'
  '"Nährflüssigkeit. **Hausenblase und andere gelatinierende Substanzen sind bei weitem nicht "\n'
  '"so gut zu gebrauchen.**»\\n\\n"',
  '"原文（**出自全集**）：«Das geeignetste Mittel, um dies zu erreichen, ist ein Zusatz von "\n'
  '"**Gelatine** zur Nährflüssigkeit. **Hausenblase und andere gelatinierende Substanzen sind "\n'
  '"bei weitem nicht so gut zu gebrauchen.**»\\n\\n"'),
 # tool-use-02：明胶 —— 出自全集
 ('"**一、明胶（Gelatine），加进营养液里。** 原文：«Das geeignetste Mittel, um dies zu erreichen, "\n'
  '"ist ein Zusatz von **Gelatine** zur Nährflüssigkeit. **Hausenblase und andere gelatinierende "\n'
  '"Substanzen sind bei weitem nicht so gut zu gebrauchen.**»\\n"',
  '"**一、明胶（Gelatine），加进营养液里。** 原文（**出自全集**）：«Das geeignetste Mittel, um dies "\n'
  '"zu erreichen, ist ein Zusatz von **Gelatine** zur Nährflüssigkeit. **Hausenblase und andere "\n'
  '"gelatinierende Substanzen sind bei weitem nicht so gut zu gebrauchen.**»\\n"'),
 # known-02：亚甲蓝 —— 出自全集
 ('"> «so verdanken wir auch hier **Ehrlich** die Einführung einer neuen, sehr zu empfehlenden "\n'
  '"Anilinfarbe, des **Methylenblaus**, welches sich ganz besonders zur Färbung von erhitzten "\n'
  '"Präparaten eignet»\\n\\n"',
  '"> «so verdanken wir auch hier **Ehrlich** die Einführung einer neuen, sehr zu empfehlenden "\n'
  '"Anilinfarbe, des **Methylenblaus**, welches sich ganz besonders zur Färbung von erhitzten "\n'
  '"Präparaten eignet»\\n"\n'
  '"（**出自全集**。）\\n\\n"'),
 # voice-01：湿室 —— 出自全集
 ('"原文：«Der Wassergehalt der Luft in dem feuchten Raum muß so reguliert werden, daß die "\n'
  '"Flüssigkeit **nicht unter dem Deckglase hervordringt** und daß das Serum **am Rande des "\n'
  '"Deckglases nicht eintrocknet**»\\n\\n"',
  '"原文（**出自全集**）：«Der Wassergehalt der Luft in dem feuchten Raum muß so reguliert werden, "\n'
  '"daß die Flüssigkeit **nicht unter dem Deckglase hervordringt** und daß das Serum **am Rande "\n'
  '"des Deckglases nicht eintrocknet**»\\n\\n"'),
 # contrast-02：命名 —— 出自全集
 ('"原文里我写的是：«die von **Pasteur 8epticäniie** und von **mir malignes Ödem** genannte "\n'
  '"Affekt ion bei Tieren»',
  '"原文（**出自全集**）：«die von **Pasteur 8epticäniie** und von **mir malignes Ödem** genannte "\n'
  '"Affekt ion bei Tieren»'),
 # voice-02 / fp-02：土豆图注 —— 出自全集
 ('"「An der Oberfläche von **Kartoffeln**, welche in Wasser aus dem **Wollsteiner Stadtgraben** "\n'
  '"faulten, gefunden」——发现于在沃尔施泰因城壕水里腐烂的土豆表面。\\n\\n"',
  '"「An der Oberfläche von **Kartoffeln**, welche in Wasser aus dem **Wollsteiner Stadtgraben** "\n'
  '"faulten, gefunden」（**出自全集**）——发现于在沃尔施泰因城壕水里腐烂的土豆表面。\\n\\n"'),
 ('"图注逐字：「An der Oberfläche von **Kartoffeln**, welche in Wasser aus dem "\n'
  '"**Wollsteiner Stadtgraben** faulten, gefunden」，配的是「Vergr. 500. Ungefärbt.」的图版，"',
  '"图注逐字（**出自全集**）：「An der Oberfläche von **Kartoffeln**, welche in Wasser aus dem "\n'
  '"**Wollsteiner Stadtgraben** faulten, gefunden」，配的是「Vergr. 500. Ungefärbt.」的图版，"'),
 # trajectory-02：环境 —— 出自全集
 ('"原文：«Mit Hilfe des **festen Nährbodens** ließ sich auch das Vorkommen der Mikroorganismen "\n'
  '"**in der Luft, im Boden und im Wasser**»',
  '"原文（**出自全集**）：«Mit Hilfe des **festen Nährbodens** ließ sich auch das Vorkommen der "\n'
  '"Mikroorganismen **in der Luft, im Boden und im Wasser**»'),
 # contrast-01：Kelbra —— 出自全集
 ('"- **Kelbra，1886**：140 头牛中 **64 头接种、76 头未接种**——"\n'
  '"「**Jede der beiden Gruppen verlor 1 Tier an Milzbrand**」，**两组各死 1 头**。接种没造成差别，遂停。\\n"',
  '"- **Kelbra，1886**：140 头牛中 **64 头接种、76 头未接种**——"\n'
  '"「**Jede der beiden Gruppen verlor 1 Tier an Milzbrand**」（**出自全集**），"\n'
  '"**两组各死 1 头**。接种没造成差别，遂停。\\n"'),
]
for a, b in SUB:
    if a in t:
        t = t.replace(a, b)
    else:
        print(f"  ⚠ 未匹配：{a[:60]}...")

# ── ② 10–15% 归还给他自己的概括，不冒充由那五条推出 ──────────────
t = t.replace(
 '"由此我给出的概括是：一次苗无损失，**二次苗带来 10 至 15% 的损失**。\\n\\n"',
 '"**我当时的概括是**：一次苗无损失，二次苗带来 10 至 15% 的损失。\\n"\n'
 '"（**说准一点**：上面列的这几组里，Kapuvar 是 5/50＝10%、Packisch 是 3/25＝12%，'
 '**最高只到 12%，推不出 15%**。那个 15% 是我把当时报上来的众多接种试验合在一起说的，'
 '**不是从这几组算出来的**——两者不能混为一谈。）\\n\\n"')

# ── ③ Robert Koch Institute 的设立名称 ─────────────────────────────
t = t.replace(
 '"**一个 Robert Koch Institute，1891 年设立，至今还在。**',
 '"**1891 年设立的那所，当时叫「传染病研究所」（Institut für Infektionskrankheiten），'
 '后来才改用我的名字**——它至今还在。')
t = t.replace('"有一个 **Robert Koch Institute**，1891 年设立，至今还在。"',
 '"1891 年设立的那所当时叫**传染病研究所**（Institut für Infektionskrankheiten），'
 '**后来才改名用我的名字**，至今还在。"')

# ── ④ 预注册框架：五处补标 ────────────────────────────────────────
MARK = '（后人的实验规范用语，不是我当年的原话）'
for old in ['"**三、先写下弃置条件。**', '"**先写下弃置条件**',
            '"**弃置判据先写下来，别等结果出来再定。**',
            '"**先写，别等结果出来再定。**']:
    if old in t:
        t = t.replace(old, old.rstrip('*"') + MARK + '**' if old.endswith('**') else old + MARK)

# ── ⑤ long-horizon-01 补埃及印度的结果 ────────────────────────────
t = t.replace(
 '"**1883–84** —— 受帝国行政派遣的 **Expedition nach Ägypten und Indien**。\\n\\n"',
 '"**1883–84** —— 受帝国行政派遣的 **Expedition nach Ägypten und Indien**；"\n'
 '"**此行的结果是分离出霍乱的病原**（我在同期记的是它的两种形态：逗点形与螺旋形）。\\n\\n"')
t = t.replace(
 '"**1883–1884 年** —— 受德国政府派遣赴埃及和印度考察霍乱，分离出霍乱弧菌。\\n\\n"',
 '"**1883–1884 年** —— 受德国政府派遣赴埃及和印度考察霍乱，分离出霍乱弧菌。\\n\\n"')

# ── ⑥ task-completion-02 去掉循环论证 ─────────────────────────────
t = t.replace(
 '"要肯定它纯，只有一条路：**拿它去做该做的事，看它做不做得成**——"\n'
 '"单独接种能复现病，再从新病例里分离出同一种。**这一步之前，任何「它是纯的」都只是没被否定而已。**")',
 '"**那怎么办？** 老实说：在只有形态学手段的年代，**「纯」是做出来的，不是验出来的**。\\n"\n'
 '"它靠的是每一步操作的严格程度——稀释够不够、取样离得够不够开、移种重复够不够多次——"\n'
 '"而不是靠事后哪一项检查给你盖章。\\n\\n"\n'
 '"（**这里不能拿「接种能复现病」来当纯度的证明**：那正是要用纯培养去做的实验，"\n'
 '"用它反过来认证纯度就是绕了个圈。这一点我在别处写「接种的若不是纯的，结果就丢掉」时"\n'
 '"已经预设了纯度是先于接种确定的。）")')

p.write_text(t, encoding='utf-8')
print('第 3 轮修正已施加')
