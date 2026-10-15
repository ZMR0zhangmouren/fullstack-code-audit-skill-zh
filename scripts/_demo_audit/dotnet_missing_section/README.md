# 反例：dotnet_missing_section

## 反例意图（契约漂移回归参考）

模拟 dotnet 审计输出树的**契约漂移**场景：route_tracer 单路由报告缺少强制章节
`## 7) Sink Summary`。该章节属于 dotnet trace 契约的 5 个强制章节之一
（dotnet-route-tracer SKILL.md 单路由报告模板），缺失即判定为契约漂移。

用于回归验证 `validate_audit.py` 检查 A（trace 契约）对"章节缺失"型漂移的检出能力。

## 目标栈

`--stack dotnet`

## 期望退出码

`1`（存在 FAIL）

## 违反的检查项

- **检查 A（trace 契约）**：`route_tracer/R1/trace_2026_08_23.md` 缺少
  `## 7) Sink Summary` 章节 → FAIL「trace 文件缺少强制章节: ## 7) Sink Summary」

## 归因设计

- trace_status: COMPLETE 为 dotnet 合法值；`## 9)` 仅引用已登记 EVID（EVID_SQL_EXEC_POINT）
- quality/（gate + pipeline_execution）与最终报告均为合规内容
- 因此 FAIL 归因单一：仅"缺 ## 7) Sink Summary"一项

## 回归命令

```bash
python scripts/validate_audit.py scripts/_demo_audit/dotnet_missing_section --stack dotnet
```
