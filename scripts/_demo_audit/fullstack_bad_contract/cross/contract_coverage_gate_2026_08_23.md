# Contract Coverage Gate

生成时间: 2026_08_23_10_30

- matched_count: 4
- frontend_only_count: 1
- backend_only_count: 1
- contract_coverage_percent: 50%
- unnormalized_rate: 5%
- contract_coverage_status: COMPLETE

<!-- 契约漂移反例（fullstack_bad_contract）：三桶计数 matched=4/frontend_only=1/backend_only=1，
     期望 percent = 4/(4+1+1) = 66.7%，但声明为 50%，
     用于触发检查 F2 的 FAIL「contract_coverage_percent 与三桶计数不符」。 -->
