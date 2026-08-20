# 花名册与中文名

## 抓全量角色

```
https://<wiki>.fandom.com/api.php?action=query&list=categorymembers
  &cmtitle=Category:Female Characters&cmlimit=500&cmnamespace=0&format=json
```

**分类名各游戏不同，先探测别猜**：
```
&list=allcategories&acprefix=Female     → Female / Female Resonators / …
```
实测：原神/崩铁/绝区零是 `Female Characters`，鸣潮是 **`Female Resonators`**（角色叫 Resonator）。

分页用 `continue.cmcontinue`，别只取第一页。

## 中文名：两条路都要走

**单靠英文站的跨语言链接不够**——实测覆盖率：原神 77/78、崩铁 33/55、**绝区零 0/45**。

1. **英文站互链**：`&prop=langlinks&lllang=zh&lllimit=500`
2. **中文站反查**：`https://<wiki>.fandom.com/zh/api.php`，用
   `generator=allpages&prop=langlinks&lllang=en` 拿到「中文页 → 英文页」再取反。
   绝区零只能靠这条。

两条合起来 60% → 87%。

**拿到的多半是繁体**（愛諾 / 亞蘿伊 / 阿蕾奇諾），用 OpenCC `t2s` 转简体：
```bash
python3 -m pip install opencc-python-reimplemented
```

## 补漏时的判据陷阱（真实事故）

对剩下没名字的角色做定向搜索，命中率会提高，但**搜索按相关度返回，很容易命中概念页**：
`topaz` 搜到「命路群像」（其实是 Fate's Ensemble）、`nova` 搜到「起蛰」（Jolt Anew）。

于是我加了反查校验：中文条目必须能链回同一个英文页。**这个判据太严**——
它抓出了那 2 个真错，但同时删掉了 7 个**对的**（黑天鹅/流萤/符玄/镜流/停云/桂乃芬/忘归人），
原因只是那些中文站条目没挂 en 互链。

**下游立刻出事**：几小时后做覆盖率比对，系统报「14 个角色不在库里」，
实际上 9 个是有角色、只是名字被删了。

**做法**：
- 判据按误判代价方向调。这里「显示了个错名」比「把有当成没有」轻得多，所以该松。
- 保留可疑项但**标记为待确认**，别直接删。
- 找**第二个独立来源**佐证（后来抖音的话题标签独立证明了流萤/镜流/符玄/黑天鹅是对的）。

## `wiki_page` 可能是 `/Lore` 子页

花名册里存的页名可能是 `Piper Wheel/Lore`、`Tsukishiro Yanagi/Lore`——
**子页上没有立绘**，要取基础页。9 个绝区零角色就是这么漏掉的，
`.split("/")[0]` 之后全部命中。

## 数据格式

```json
{"game":"wuwa","game_zh":"鸣潮","source":"…","fetched":"2026-08-20",
 "characters":[{"id":"camellya","name_en":"Camellya","name_zh":"椿",
   "game":"wuwa","game_zh":"鸣潮","wiki_page":"Camellya",
   "status":"pending","refs":[],"refs_status":"none"}]}
```
`id` 用 `re.sub(r"[^a-z0-9]+","-",title.lower()).strip("-")`。

## 第三条路：英文站 infobox 的 `zhs` 字段

两条互链路都走完还缺的（鸣潮实测缺 5 个：baizhi / chixia / jianxin / sanhua / youhu），
去英文页的 wikitext 里取 `zhs`——中文站没挂 en 互链时它仍然在。

```python
wt = api({"action": "parse", "page": page, "prop": "wikitext", "format": "json"})
zh = re.search(r"zhs\s*=\s*([\u4e00-\u9fff·]{1,10})", wt).group(1)
```

**取第一个 `zhs`，不是最后一个**：有的页面有两个——第二个是 `realname` 的中文
（Chixia 的第二个 `zhs` 是「马小芳」，角色名是「炽霞」）。

加上这条之后鸣潮 43 人全部补齐。

## 重跑会丢名字：只补不覆盖

同一个脚本第二次跑，因为 wiki 侧偶发不返回，**比上一版少了 5 个**
（firefly / jingliu / fu-xuan / black-swan / odette 全是对的）。
直接覆盖输出文件就把它们丢了。

```python
merged = dict(new)
for k, v in old.items():
    merged.setdefault(k, v)      # 新的没有的才用旧的；有冲突先打印出来看
```
