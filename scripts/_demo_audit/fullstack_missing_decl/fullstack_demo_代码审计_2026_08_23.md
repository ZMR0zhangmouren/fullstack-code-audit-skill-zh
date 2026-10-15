# fullstack-demo 项目全栈代码审计报告

生成时间: 2026_08_23_12_00

## 1) 完成态四声明（全栈固定模板）

- dotnet_api_coverage_status: COMPLETE
- node_api_coverage_status: COMPLETE
- contract_coverage_status: COMPLETE

## 2) 审计范围

dotnet_source_path 与 node_source_path 双栈全量审计，跨端契约对账已完成。

<!-- 演示问题（检查 F 应 FAIL）：故意缺失 audit_surface_status 声明，
     四声明必须齐全，禁止用单一“已完成”替代 -->
