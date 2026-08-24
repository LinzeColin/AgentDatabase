# Integrated Market Cycle｜v0.0.0.3

本文件取代 v0.0.0.2 的旧 T/M 宏循环。唯一 active contract：

```text
一轮：T1 -> C1 -> S1 -> C2 -> P1 -> C3
一组：连续三轮
一次 Run：连续三组
```

T/S/P 每次调用都完整执行三段内部 run；三个公共别名都启动同一个完整 Run。旧编排只存在于 Changelog 和来源证据，不得作为执行依据。
