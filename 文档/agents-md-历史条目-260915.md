# AGENTS.md 历史条目（2026-09-15 移出）

> 这两节的**规则**已压缩进 `AGENTS.md`，**规则真源**是 `GithubProject/README.md` 铁律 2。
> 这里原样保留当时的完整实测记录与代价复盘，供追溯。

## worktree 位置：桌面版**没有**「Worktree location」这个设置（2026-08-13 实测，Claude Code 2.1.212）

**结论**：`GithubProject/README.md` 里长期写着「桌面版可在 Settings → Claude Code → Worktree location
指到 `~/Documents/Codex/GithubProject/_scratch/`」—— **那个设置不存在**。二进制里 0 处该文案；
`~/.claude.json`、`~/.claude/settings.json`、桌面版 `claude_desktop_config.json` 里都没有对应键；
搜「值为 `~/Documents/Codex` 的配置项」也是 0 处。这条是当初某个 agent **猜的**。

真实规则是**算出来的**：worktree 固定落在 `<仓的祖父目录>/<仓名>/<worktree名>`。
所以根指到 `GithubProject/AgentDatabase` 时，worktree 落在 `~/Documents/Codex/AgentDatabase/<名字>`，
**在 `GithubProject/` 外面，违反铁律 2**。证据在桌面版自己的登记表
`~/Library/Application Support/Claude/git-worktrees.json` 的 `untrackedDirGc.roots`，
明写着 `~/Documents/Codex/AgentDatabase` 和 `~/Documents/Codex/MetaDatabase` 两个根。

**代价**：这条铁律从写下那天起就不可执行，而后来每个 agent（包括我）都把它当「Owner 定的规矩」引用，
**谁也没去点开看一眼**。我还差点把「你去 Settings 改」当成 Owner 的待办交回去 ——
要他去改的那个东西本来就是 agent 写错的，交回去等于让他替我们的错买单。

**怎么办**（README 已改成这两条）：
① **手开 worktree，别用桌面版自动的** —— 在主树跑 `git worktree add ../_scratch/<repo>-<任务名> -b <分支> origin/main`。
本机 MetaDatabase 的 worktree 全在 `_scratch/` 下就是因为都是手开的，**这条一直有效，只是从没被写下来**。
② 已被自动开在外面的照常能用，但**收尾要多确认一步** `~/Documents/Codex/<REPO>/` 空了 ——
否则会留下 `git worktree list` 里都没有的空壳目录（2026-08-10 留下过一个，里面躺着一份文件）。

**自查**（已验四个方向：主树不报、`_scratch/` 下不报、`NotGithubProject/` 下报、别处报）：

```bash
ROOT=$(cd ~/Documents/Codex/GithubProject && pwd -P)   # 必须 pwd -P 取真实路径
for r in "$ROOT"/*/; do
  [ -d "$r/.git" ] || continue
  git -C "$r" worktree list --porcelain 2>/dev/null | awk -v ROOT="$ROOT/" -v R="$(basename "$r")" \
    '/^worktree /{p=substr($0,10); if (index(p, ROOT) != 1) print "✗ " R ": " p}'
done
```

> 这条命令的两个坑都是造夹具才炸出来的，**别改回去**：
> ① `!~ /GithubProject/` 是**子串**匹配，会放过 `/x/NotGithubProject/y`，也会把主树自己误报；必须 `index(p,ROOT)!=1` 做前缀。
> ② `ROOT` 不 `pwd -P` 的话，在有软链的环境（macOS `/tmp`→`/private/tmp`）**100% 全报** ——
> `git worktree list` 返回的是解析过软链的路径。本机 `~/Documents/` 没软链所以碰巧不发作，**换台机器就炸**。
>
> **不止桌面版会这样**：2026-08-21 跑这条自查抓到
> `/Users/linzezhang/.codex/worktrees/521b/MetaDatabase` —— **Codex 把 worktree 放在 `~/.codex/worktrees/`**，
> 又是另一个 `GithubProject/` 外的根。所以这条自查要**定期跑**，别只在换 agent 时想起来。

## 报路径一律用绝对路径 —— 剥前缀等于报错位置

**结论**：交付运维金库时我为了好看用 `sed 's|.*/GithubProject/|  |'` 把前缀剥掉，打印成
`_protected/ops_vault/LINZE_OPS_VAULT_20260813.tar.gz`。界面把相对路径按**会话 cwd** 渲染成可点链接，
而那个会话的 cwd 恰好是一棵开在错位置的 worktree —— **Owner 点开看到的是一条指向公开仓工作树的凭据路径，据此判我泄漏**。

文件从头到尾都在正确的 `GithubProject/_protected/` 下（`find` 全盘只有 3 处，全对）。**错的是我的汇报。**

**代价**：他必须先花时间**证伪我**，才能继续干活。这类错比内容错更贵 —— 内容错会被判据抓到，坐标错不会。

**规矩**：① 报路径一律绝对路径，不 sed、不省略、不为对齐截断；
② **凭据 / 备份 / 交付物**这三类的位置尤其如此，报错位置是安全事故级的；
③ 想让输出好看就用表格或缩进，**不要动路径本身的字符**；
④ 自查加一条：**我打印的每条路径，从 Owner 的 cwd 出发点开，落在我以为的地方吗？**

> 同一个错第二天在别人身上复现：Codex 报「`_protected` 里没东西」，因为它在
> `_scratch/metadatabase-abd-v0001-s11-p01/` 里找相对路径 —— **`_protected/` 在 `GithubProject/` 根下，往上两级**。
> 给别的 agent 指路时也只给绝对路径。
