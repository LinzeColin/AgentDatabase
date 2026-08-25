# Codex 最后一公里执行合同 — v0.0.0.2

## 目标

将本压缩包中的完整 `video-prompt-compiler` 原样落入：

```text
LinzeColin/AgentDatabase/CodexSkills/registry/codex/video-prompt-compiler/
```

Codex 不重新研究、不重写产品、不覆盖现有 `prompt-compiler`。

## 一个执行包

1. 获取仓库当前状态并确认目标目录；
2. 目标不存在：复制本包完整目录；目标已存在：先对比版本与文件，再按用户指令更新，不擅自删除其他文件；
3. 在 Skill 根目录运行以下验证；
4. 只修复路径/导入/仓库环境造成的最后一公里问题，不改产品语义；
5. commit、push，并按仓库实际惯例进入 main 或创建 PR；
6. 只回报路径、修改文件、验证结果、commit/PR/merge、未运行项。

## 验证命令

```bash
python3 scripts/validate_package.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/route_request.py --text '把40秒竖屏十字轴激光熔覆原片剪成18秒企业片' --format markdown
python3 scripts/compile_request.py --text '机器人沿工件曲面做8秒熔覆镜头' --model 'Seedance 2.0' --format json
python3 scripts/score_prompt.py --file examples/industrial_cladding.md --source-idea '工业熔覆镜头' --route reference_to_video --preset industrial --model 'Seedance 2.0'
```

最后一条若示例存在硬门槛错误，应记录事实并按包内语义修复示例；不得通过放宽硬门槛掩盖问题。

该路由样例必须显示 `route=footage_edit`、`source duration=40`、`target duration=18`；任一字段不符都应停止落库并回报。

## 禁止

- 不引入 API key 或调用收费模型；
- 不改用户真实素材；
- 不把本地测试称为外部 Verifier PASS；
- 不把 `NOT_RUN` 改为 PASS；
- 不恢复未经核验的版本映射；
- 不引入哈希/校验和流程；
- 不做与任务无关的框架重构。
