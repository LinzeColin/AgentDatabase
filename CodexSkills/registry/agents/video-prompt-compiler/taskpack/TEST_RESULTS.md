# Test Results — v0.0.0.2

## Scope

本报告只记录包内可重复的离线结构、路由、IR、评分、安装和端到端样例结果。它不代表真实视频模型成片、人工观看或外部独立验收。

## Final execution

| 检查 | 结果 | 关键事实 |
|---|---|---|
| Package inventory / JSON / Python syntax | `PASS` | `scripts/validate_package.py` 返回 PASS |
| Unit and regression tests | `PASS — 52/52` | 路由、IR、模型注册表、评分、硬门槛、安装与 fixtures 全部通过 |
| Custom installation | `PASS` | 测试安装保留运行文件、`research/`、`taskpack/` 与 `.ramify/HANDOFF.md` |
| Footage routing sample | `PASS` | `footage_edit`; source `40s`; target `18s`; output `director` |
| VideoPromptIR sample | `PASS` | source `40s`; target `18s`; MiniMax Design 状态 `PLATFORM_VERIFY_AT_RUNTIME` |
| Industrial structural scoring | `PASS` | `READY_FOR_MODEL_TEST`; `89.0%`; hard-gate errors `0` |
| Hard-gate rejection | `PASS` | 形容词堆积样例被 `ADJECTIVE_SOUP`、`NO_OBSERVABLE_ACTION`、`INDUSTRIAL_NO_RELATION` 阻断；命令返回非零 |
| Final archive clean extraction and rerun | `PASS — 52/52` | 从压缩包独立解压后，包清单、安装、路由、IR、正反评分样例全部复现 |

## Commands

```bash
python3 scripts/validate_package.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/route_request.py --text '把40秒竖屏十字轴激光熔覆原片剪成18秒企业片，保留原设备和工人' --format json
python3 scripts/compile_request.py --text '把40秒竖屏十字轴激光熔覆原片剪成18秒企业片，保留原设备和工人' --model 'MiniMax Design' --format json
python3 scripts/score_prompt.py --file examples/industrial_cladding.md --source-idea '机器人沿十字轴曲面做激光熔覆，真实克制，最后停在连续熔覆带上' --route reference_to_video --preset industrial --model 'MiniMax H3'
python3 scripts/score_prompt.py --text '高级，震撼，电影感，科技感，8K，masterpiece' --source-idea '工业设备工作镜头' --route text_to_video --preset industrial --model 'Seedance 2.0'
```

## Defect found and closed before packaging

端到端样例曾把“把真实素材剪成……”误路由为 T2V，并可能混淆源素材时长与目标成片时长。当前实现增加中文剪辑意图与双时长解析，并加入固定回归：`40s source → 18s target`；仅给源时长时，目标保持 `UNKNOWN`。

## Evidence boundary

- Structural specification score: `RUN`
- Native-model generation: `NOT_RUN`
- Human visual review: `NOT_RUN`
- External Verifier: `NOT_RUN`
- AgentDatabase commit/push/merge: `NOT_RUN`
