# 反例：fullstack_bad_contract

## 反例意图（契约漂移回归参考）

模拟全栈审计输出树的**契约漂移**场景：cross/contract_coverage_gate 的
三桶计数与 percent 不一致——`matched_count=4 / frontend_only_count=1 / backend_only_count=1`
（total=6），期望 `contract_coverage_percent = 4/6 = 66.7%`，但声明为 `50%`。

契约对齐规则（cross-stack-contract-mapper SKILL.md）：percent 必须等于
`matched/(matched+frontend_only+backend_only)`。声明值与期望值偏差超过 0.5% 即判定漂移。

用于回归验证 `validate_audit.py` 检查 F2（contract 三桶计数）对"计数与 percent 失配"型漂移的检出能力。

## 目标栈

`--stack fullstack`

## 期望退出码

`1`（存在 FAIL）

## 违反的检查项

- **检查 F2（contract 三桶计数）**：`cross/contract_coverage_gate_2026_08_23.md`
  的 `contract_coverage_percent: 50%` 与三桶计数不符（期望 66.7%）→
  FAIL「contract_coverage_percent=50.0% 与三桶计数不符（期望 66.7% = matched/total）」

## 归因设计

- 输出树结构参照合规样例 fullstack_ok：dotnet/ 与 node/ 子树的 gate 产物、
  最终报告四声明均为合规内容
- contract gate 的 contract_coverage_status 与 unnormalized_rate 均正常声明
- 因此 FAIL 归因单一：仅"percent 与三桶计数失配"一项

## 回归命令

```bash
python scripts/validate_audit.py scripts/_demo_audit/fullstack_bad_contract --stack fullstack
```
