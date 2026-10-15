# Pipeline Execution

生成时间: 2026_01_01_10_20

- pipeline_execution: COMPLETED
- coverage_mode: FULL

| skill_name | skill_type | execution_status | findings_status | primary_outputs | depends_on | notes |
| ---------- | ---------- | ---------------- | --------------- | --------------- | ---------- | ----- |
| dotnet-route-tracer | route_tracer | COMPLETED | FOUND | route_tracer/* | route_mapping | - |

<!-- 演示冲突：api_coverage_status=PARTIAL 且 percent=80%，但 pipeline_execution=COMPLETED，应触发检查 C FAIL -->
