# 数据、Oracle 与封印合同

## 五类数据

| 文件 | 用途 | 搜索阶段可见 |
|---|---|---|
| `train.jsonl` | 读取失败轨迹、反思和候选生成 | 是 |
| `validation.jsonl` | 同预算筛选候选与 Pareto 前沿 | 是 |
| `final_test.jsonl` | 候选冻结后的独立最终比较 | 否 |
| `regression.jsonl` | 保证旧能力不退化 | 搜索结束后 |
| `redteam.jsonl` | 越权、注入、泄露和拒绝边界 | 搜索结束后 |

案例编号不得跨 split 重复。`dataset_seal.json` 保存每个文件的 SHA-256、记录数和封印时间。任何修改都会使封印失效。

## 每行最低字段

```json
{
  "id": "case-001",
  "task_id": "任务簇",
  "input": "实际输入",
  "must_include": ["必须出现"],
  "must_not_include": ["禁止出现"],
  "assertions": [
    {"type": "contains", "value": "必须出现", "hard": true}
  ],
  "reference": "可选真值答案",
  "rubric": "可选语义评分规则",
  "synthetic": false,
  "metadata": {}
}
```

支持断言：`contains`、`not_contains`、`regex`、`not_regex`、`is_json`。自定义业务 Oracle 可通过案例字段和主运行时扩展。

## 评分顺序

1. 硬断言和输出结构；
2. 自定义 Oracle / 参考真值；
3. 安全边界；
4. 语义质量；
5. 长度、成本和稳定性。

硬失败不能被高语义分抵消。评分报告必须含均值、最差值、方差、样本方差、逐案例、逐任务、维度分数和硬失败明细。

## 合成数据边界

模型生成的案例可用于打通管线和发现明显缺陷，但不等于真实业务证据。最终测试含合成案例时，最高只能实验性通过，不能正式发布。
