# Coverage Consistency Check
生成时间: 2026_01_01_12_00

## 对比文件
- quality/api_coverage_gate_2026_01_01_10_10.md
- quality/pipeline_execution_2026_01_01_10_20.md
- route_mapping/routes_2026_01_01_10_00.md
- exploit_chain/exploit_chains_2026_01_01_11_30.md
- demo_代码审计_2026_01_01_12_00.md

## 一致性矩阵
| 字段 | gate | pipeline_execution | routes | exploit_chain | final_report | 一致性 |
|---|---|---|---|---|---|---|
| coverage_mode | FULL | FULL | N/A | FULL | FULL | PASS |
| api_coverage_status | PARTIAL | PARTIAL | N/A | PARTIAL | PARTIAL | PASS |
| api_coverage_percent | 80% | 80% | N/A | 80% | 80% | PASS |
| count_self_check | N/A | N/A | PASS | N/A | N/A | PASS |
| exploit_chain_consistency_check_counts | N/A | N/A | N/A | PASS:2 | PASS:2 | PASS |

## 冲突项（如有）
- 无

## 结论
- final_status: PASS
- notes: 关键字段一致，可交付。
