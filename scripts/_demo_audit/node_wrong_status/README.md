# 反例：node_wrong_status

## 反例意图（契约漂移回归参考）

模拟 node 审计输出树的**契约漂移**场景：route_tracer 单路由报告 10 章节骨架齐全，
但 `trace_status: COMPLETE` 不在 node 五态值域内
（合法值域：NOT_STARTED / IN_PROGRESS / DONE_OPEN / DONE_CLOSED / BLOCKED，
见 node-route-tracer SKILL.md）。

`COMPLETE` 是 dotnet 侧合法值而非 node 侧值——该反例同时回归"栈间状态值域混淆"
型契约漂移：若 node 侧误用 dotnet 的 COMPLETE 语义，必须被检查 N 拦截。

用于回归验证 `validate_audit.py` 检查 N（node trace 契约）对"trace_status 值域外"型漂移的检出能力。

## 目标栈

`--stack node`

## 期望退出码

`1`（存在 FAIL）

## 违反的检查项

- **检查 N（node trace 契约）**：`route_tracer/R2/trace_2026_08_23.md` 的
  `trace_status: COMPLETE` 非五态值 → FAIL「node trace_status 值非法: COMPLETE」

## 归因设计

- 5 个最小章节（参数可控性矩阵 / Sink 定位 / Sink Summary / Trace 完整性声明 /
  Sink Evidence Type Checklist）齐全；checklist 仅引用已登记 EVID（EVID_NODE_NOSQL_QUERY_POINT）
- quality/（gate + pipeline_execution）与最终报告均为合规内容
- 因此 FAIL 归因单一：仅"trace_status 值非法"一项

## 回归命令

```bash
python scripts/validate_audit.py scripts/_demo_audit/node_wrong_status --stack node
```
