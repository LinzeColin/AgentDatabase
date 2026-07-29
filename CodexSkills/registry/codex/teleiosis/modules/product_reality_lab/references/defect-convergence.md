# Defect Convergence

## 稳定 Defect ID

同一根因的多个症状应聚类；ID 不因修复尝试变化。

## 发现曲线

每轮记录：

- 新增 unique valid defects；
- P0/P1/P2/P3；
- duplicate/false-positive；
- method/source；
- actions/time/tokens/compute；
- covered critical edges；
- field escapes。

## 自适应预算

高严重度、独特缺陷收益高的方法升权；长期重复或低价值的方法降权。Field escape 对应路径和故障模型自动升权。

## 残余未知估计

可选用两个或多个相对独立的方法（例如 deterministic state model、model exploration、human review）的 defect overlap 做 capture-recapture 辅助估计。必须记录独立性假设和不确定性；它不是发布证明。

## 修复闭环

Target regression → neighborhood regression → critical suite → mutation/fault negative control → evidence hash update。
