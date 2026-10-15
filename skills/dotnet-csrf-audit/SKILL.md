---
name: dotnet-csrf-audit
description: .NET CSRF 审计工具。识别状态变更入口的 Antiforgery 保护缺失、校验绕过与不一致配置风险。
---

# .NET CSRF 审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与 Antiforgery、Cookie 认证、跨站提交、状态变更入口和例外白名单相关的共享抓手
- 若项目存在 CsrfHelper、AjaxWrapper、MutationGateway、AdminActionService 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（用于对齐状态变更入口、参数来源与 `route_id`）
- 可选：`auth_audit/auth_mapping_{timestamp}.md`（用于补充认证态、匿名入口与权限边界）
- trace-gate 场景下优先消费：`route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline` 执行，当前专项引用的 `route_id` 应与 `cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- 状态变更接口（POST/PUT/PATCH/DELETE）是否启用 Antiforgery 校验
- API Controller 默认不启用 Antiforgery 的风险（Cookie 认证 + API 组合）
- [IgnoreAntiforgeryToken] 标记的接口是否确实无状态变更副作用
- Content-Type 绕过：text/plain 不触发 CORS preflight 的利用场景
- SPA/Ajax 场景下 Antiforgery token 的传递与校验机制
- Blazor Server 事件、SignalR Hub 方法、GraphQL Mutation 的 CSRF 防护
- 子域名 Cookie 注入导致 token 覆盖的可能性

## 证据引用

- EVID_CSRF_STATE_CHANGE_HANDLER_EXEC
- EVID_CSRF_TOKEN_SOURCE
- EVID_CSRF_TOKEN_VERIFY
- EVID_CSRF_BYPASS_BRANCH

## 枚举规则（强制细化）

- 枚举所有状态变更接口：POST、PUT、PATCH、DELETE、GraphQL Mutation、Blazor Server 事件、副作用 Hub 方法
- 优先搜索 ValidateAntiForgeryToken、AutoValidateAntiforgeryToken、IgnoreAntiforgeryToken、IAntiforgery、cookie auth + API 组合使用位置
- 枚举前端表单、Ajax、SPA、GraphQL、SignalR、iframe 提交、文件上传和多部件请求路径
- 对每个状态变更入口记录：认证方式、token 来源、校验位置、例外规则、content-type 分支、是否跨站可触达

## Barrier 验证矩阵（强制）

按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 三级标准评估：

| 等级 | 检查项 | 通过标准 | 失败降级 |
|------|--------|----------|----------|
| 一级 | 状态变更入口可触达 | POST/PUT/PATCH/DELETE/Mutation/Hub 等入口存在且可跨站触发 | BLOCKED → 非状态变更入口，专项结束 |
| 二级 | Token 校验链完整 | token 生成、传输、校验三段证据齐全且无断裂 | BLOCKED → 结论降级为 `⚠️待验证/环境依赖` |
| 三级 | 绕过分支不可达成 | 无有效的 content-type/白名单/框架分支绕过路径 | PARTIAL → 仅输出绕过假设与验证步骤 |

## 二阶段判定流程（强制）

- **阶段 1（初筛命中）**：命中状态变更入口 + token 来源可控或缺失，输出 `命中ID：M{hash}`。
- **阶段 2（精筛确认）**：
  1. 逆向追踪 token 生成-传输-校验三段链路；
  2. 检查 [IgnoreAntiforgeryToken] / content-type 分支 / 白名单例外的绕过条件；
  3. 若三级 Barrier 全部通过 → `确认漏洞`；任一失败 → 按矩阵降级。

## 判定规则与优先级（强制）

1. **确认漏洞**：状态变更入口可触达 + token 校验链断裂或完全缺失 + 绕过分支可达成。输出 `确认漏洞`。
2. **待确认**：入口可触达但 token 链部分证据缺失，或绕过条件依赖特定环境。输出 `待确认`。
3. **误报/无风险**：入口非状态变更（如纯 GET 只读），或 token 校验链完整且无可绕过分支。输出 `误报` 并给出判定依据。

## 测试建议与最小触发条件（强制）

- **最小触发条件**：
  - 存在状态变更请求入口（POST/PUT/PATCH/DELETE/Mutation/Hub）
  - 请求可携带目标站点 Cookie（SameSite=None/Lax 或子域名注入）
  - 无有效 Antiforgery token 校验，或校验可被绕过
- **测试用例建议**：
  - Happy Path：正常带 token 请求被接受，不带 token 被拒绝
  - 边界/歧义：Content-Type: text/plain 绕过 preflight、子域名 Cookie 覆盖、白名单接口状态变更副作用
- 每条命中输出追加 `命中ID：M{hash}` 和 `test_id：T{hash}`，用于回溯。

## 工作流（输入→执行→输出）


## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（状态变更入口确认）**：必须先锁定具备副作用的入口（POST/PUT/PATCH/DELETE/Mutation/Hub）。
- 🔴 **CHECKPOINT B（token链确认）**：必须给出 token 生成、传输、服务端校验三段证据。
- 🔴 **CHECKPOINT C（绕过分支确认）**：必须明确 content-type/例外白名单/框架分支是否可绕过校验。
- 🛑 **STOP**：若 token 校验链不完整，结论降级为 `⚠️待验证/环境依赖`，禁止输出已确认 CSRF。

## 失败场景与兜底（if-then）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| 状态变更入口识别不完整 | 补齐 POST/PUT/PATCH/DELETE/Mutation/Hub 入口清单 | 先保留高风险入口为待验证，不给强结论 |
| token 生成-传输-校验链断裂 | 分别补齐三段证据并核对分支条件 | 结论降级 `⚠️待验证/环境依赖` |
| 白名单/content-type 绕过证据不足 | 逐项核对白名单与请求类型分支 | 仅输出可疑绕过路径与验证步骤 |

🔴 **STOP：任一兜底触发时，禁止输出“已确认 CSRF”。**

## 资源引用与可达性校验（强制）

- 必引共享索引：`skills/shared/DOTNET_AUDIT_GRABBER_INDEX.md`（抓手来源）与 `skills/shared/EVIDENCE_POINT_IDS.md`（证据口径）。
- 输出口径校验：落盘路径与命名必须对齐 `skills/shared/IO_PATH_CONVENTION.md`，不得自定义偏离目录。
- 证据一致性校验：若引用分级结论，需与 `skills/shared/SEVERITY_RATING.md` 保持一致。
- 可达性检查：提交前至少确认一次关键引用文件可访问（例如 `DOTNET_AUDIT_GRABBER_INDEX.md`、`IO_PATH_CONVENTION.md`）。

## 实测用例与通过标准（强制）

- 每次产出前至少执行 2 条典型测试用例（happy path + 边界/歧义场景各 1 条），并记录预期与实际差异。
- 默认要求 `full_test >= 1`；若只能 `dry_run`，必须在结论中标记 `confidence=LOW`，并给出补测计划与负责人。
- 通过标准：关键字段齐全、证据链可回溯、结论级别与门禁状态一致；任一失败则禁止标记“已通过/可交付”。

## 整体架构与冗余控制（强制）

- 章节组织必须保持三层骨架：`输入约束` → `执行步骤` → `输出与验收`，不得缺层或跨层混写。
- 单段建议不超过 6 行；同义规则禁止重复出现两次以上，重复内容需合并到唯一真源章节。
- 禁止 AI 腔与空话衔接词堆叠（如“首先/其次/最后/综上/说白了/换句话说”）；发现即改为可执行语句。

## 质量门禁与评估一致性（强制）

- 产出前必须执行最小门禁自检：`输入完整性`、`关键证据命中`、`输出路径合法` 三项全部为 PASS。
- 若存在 `关键证据缺失`、`链路未闭合`、`consistency_check_status=BLOCKED` 任一条件，结论必须降级为 `BLOCKED`，禁止输出“确认可利用/可交付”。
- 报告中必须显式记录：`gate_status`、`blocked_reasons`、`recheck_action`，并与 `quality/*` 产物可回溯对齐。

## 不要做的事（反例黑名单）

- 反模式：把“登录态存在”当作“CSRF 不成立”。正确做法：检查跨站请求是否可携带凭据。
- 反模式：忽略 JSON/API/Mutation/Hub 的副作用入口。正确做法：覆盖所有状态变更面。
- 反模式：未验证 token 生成-传输-校验闭环。正确做法：三段证据缺一不可。
- 反模式：例外白名单不审计。正确做法：逐项核对白名单边界与绕过条件。

## 可执行参数与输出模板（强制）

- 审计结论等级：`已确认` / `⚠️待验证` / `不适用`（三选一，禁止留空）。
- 证据最小集：至少包含 `入口点`、`可控参数`、`关键调用`、`安全边界`、`缺失证据` 五项。
- 输出文件命名：统一使用 `{topic}_{timestamp}.md`，并与 `IO_PATH_CONVENTION.md` 对齐。
- 禁止使用软化措辞：如“可能有风险/建议关注/视情况而定/大概率”等；证据不足时必须明确写 `⚠️待验证` 与下一步补证动作。

最小输出片段（可直接复用）：

```md
- 审计结论等级：已确认
- 证据最小集：入口点=...；可控参数=...；关键调用=...；安全边界=...；缺失证据=无
- 下一步动作：若存在缺口，补 trace_id=... 的参数传播证据
```

## 输出

- vuln_audit/csrf_{timestamp}.md
- 可选：vuln_poc/csrf_{timestamp}.md（已确认 / 待验证 / 环境依赖 PoC；如不适合直接构造请求，至少给出验证步骤）
