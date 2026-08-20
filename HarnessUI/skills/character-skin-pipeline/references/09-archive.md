# 归档：NAS 与 git

## NAS 结构（成品与素材并列）

```
smb://192.168.0.1/share/03_资料库/MetaData/HarnessUI/
  <游戏中文>/<角色>/refs/          # 锚图与出处（source.json）
  <游戏中文>/<角色>/skins/<变体>/  # light.png / dark.png / meta.json
                                    # 以及 *.rejected-N.png（被替换的旧版）
```

成品放在**它所依据的素材旁边**，不另建一棵树——
一个角色目录就能回答「我们有什么、做出了什么」。

`meta.json` 记：task / game / character / variant / model / size /
pack_version / acceptance(含每张的验收指标) / generated 日期。

## SMB 的三个坑（第一个最致命）

### 1. `shutil.copyfile` 会写出「大小正确、内容全 0」的文件，并返回成功

macOS 上 `shutil.copyfile` 优先走 `fcopyfile`（clone）。在 smbfs 上它**创建一个
尺寸完全正确、内容全是零字节的文件，且不抛任何异常**。

2026-08-20 实测：614 张已归档成品里 **376 张是全 0**，当初的归档脚本一个错都没报。
用户以为有备份，实际 61% 是空壳。

```python
# ✗ 在 SMB 上会静默写出全 0
shutil.copyfile(src, dst)

# ✓ 显式分块 read/write + fsync
with open(src, "rb") as reader, open(dst, "wb") as writer:
    for chunk in iter(lambda: reader.read(4 * 1024 * 1024), b""):
        writer.write(chunk)
    writer.flush()
    os.fsync(writer.fileno())
```

**并且每张都要读回来核对**（SHA-256 或至少魔数），
把「校验通过」当成写入成功的唯一判据。exit code 0 不算数。

**魔数校验不够。** 我先用「PNG 头合法」判过一次，得到「2647 张 0 坏」；
随后按 SHA-256 逐张比对，又拷回去 **266 张**——其中约 170 张是魔数看不出来的
（只写了前几 KB 的截断文件，头是合法的）。

**判据强度决定你看到的世界。** 归档的唯一可信判据是和源文件比摘要：

```python
def digest(path):
    hasher = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()
```

**skip 判据也要比内容，不能比大小。** 原来的归档脚本用
`target.stat().st_size == source.stat().st_size` 判「已完成」，
于是那 376 个空壳每次重跑都被跳过——**坏了也永远不会被发现**。

### 2. 连续写会把它打崩

612 个 6-8MB 文件背对背拷，实测 **240 个报 `Input/output error`**，
而同一个文件一分钟后手动拷只要 0.9 秒——是被打崩不是坏了。
做法：**四次重试 + 指数退避 + 每 8 个文件歇 0.4 秒**。加了之后失败 0。

### 3. 覆盖同名文件的 rename 会失败

`mv a.png.part a.png` 在目标已存在时报 I/O 错误，而且会**先把目标删掉**——
中途失败就是两边都没有。做法：先确认目标名空出来再写。

### 4. 挂载点会坏，但那不等于数据没了

持续大量读写之后，挂载点会进入一种「还在 `mount` 列表里、`ls` 却报路径不存在」
的状态，某个目录甚至只列得出一部分子目录。**这时候不要当成删除。**

一步判据：从**另一条路径**看同一个共享（另一个挂载点、或者 `smbutil view`
确认服务端还在）。实测数据一张没少，坏的只是那个挂载点的目录缓存。

> 另：别在 SMB 上跑 `du -sh` / 全量 `find`，会超时；要数数就按子目录分别数。

## git

**二进制不进 git。** 母版 4.8GB、显示图 100MB+ 都归档在 NAS。
仓里只放目录与治理：

```
HarnessUI/
  README.md  ROADMAP.md  DEPLOY.md
  research/     花名册、中文名、素材源调研
  delivery/     manifest-<version>.json、acceptance-<version>.json、catalog.json
  tools/        全部脚本
  dsh-plugin/  kimi-shell/  menubar-app/   宿主侧源码
  .gitignore    output/ skin-assets/ *.png *.webp *.zip .oaikey
```

`acceptance-<version>.json` 是逐张的验收记录（status/attempts/metrics/fails），
**不要把台账原样提交**——它含 key 路径和几 MB 的 prompt。

### sparse-checkout 会静默拦下新目录

`git add` 报 "paths … outside of your sparse-checkout definition" 时，
文件**没有进暂存区**，而 `git push` 仍会成功（推的是空提交）。
先 `git sparse-checkout add <目录>` 再 add。

### 推送闸门

仓库可能有 pre-push 钩子（体积闸、全仓体检）。被无关的检查拦下时，
用它文档里给的跳过方式，**并在回复里明说跳过了什么、为什么无关**——
先确认改动范围（`git diff --name-only origin/main..HEAD`）。

## 绝对不要

**把唯一副本放在会话临时目录。** 母版一度只存在 `/private/tmp/.../scratchpad`，
而运行时目录的三个软链正指着那儿。/tmp 一清，4.8GB 和验收页全部大图一起没。
运行时素材放 `~/.harness-ui/`，母版另有 NAS 备份。
