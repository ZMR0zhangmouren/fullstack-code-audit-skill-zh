---
name: dotnet-aspnet-core-audit
description: ASP.NET Core 框架专项审计工具。针对中间件顺序、配置绑定、鉴权、CSRF、CORS、静态文件、安全头和运行时选项进行白盒审计。
---

# ASP.NET Core 框架专项审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与 aspnet-core 相关的入口定义、绑定转换、前置控制、敏感操作、安全配置抓手
- 若项目存在框架二次封装、统一扩展方法、平台基座或宿主包装层，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（如已由 `dotnet-route-mapper` 生成，用于对齐入口、参数绑定与 `route_id`）
- 可选：`auth_audit/auth_mapping_{timestamp}.md`（如需对齐匿名入口、P0/P1 分桶与授权边界）
- 可选：`route_tracer/{route_id}/trace_{timestamp}.md` 与 `route_tracer/{route_id}/trace_summary_{timestamp}.md`（如需将中间件/宿主控制面与具体入口、副作用链做交叉引用）

## 重点检查

- Middleware 顺序：UseForwardedHeaders、UsePathBase、UseRouting、UseCors、UseAuthentication、UseAuthorization、UseSession、UseEndpoints 的先后关系
- Antiforgery、CORS、静态文件、异常页、安全头、HSTS、HTTPS 重定向、Rate Limiting、Output Caching 的配置与覆盖范围
- Minimal API、Endpoint Filter、Route Group、MapFallback、MapWhen、branch pipeline 与匿名/授权混用边界
- appsettings.json、web.config、Options 绑定、IOptionsSnapshot、IOptionsMonitor、自定义配置绑定器与模型验证缺口
- Kestrel、IIS、反向代理、容器、PathBase、HostFiltering、ForwardedHeaders 的信任边界与环境差异
- Swagger、HealthChecks、Prometheus、Hangfire、SignalR、StaticFile、Razor Runtime Compilation 等功能组件的暴露面

## 枚举规则（强制细化）

- 枚举 Program.cs、Startup.cs、扩展方法和宿主初始化代码中的中间件注册顺序，记录每个 Use/Map/Run 分支的进入条件、顺序位置和是否存在短路
- 优先搜索 appsettings.json、web.config、UseRouting、UseAuthentication、UseAuthorization、UseCors、UseSession、UseEndpoints、MapGroup、MapControllers、MapFallback、MapWhen、UseWhen、AddAntiforgery、AddCors、AddAuthentication、AddAuthorization
- 枚举 Minimal API、Controller Endpoint、HealthChecks、Swagger、StaticFiles、Hangfire、SignalR、GraphQL、Prometheus 等暴露端点，记录匿名可达性、环境开关、PathBase 与反向代理前缀影响
- 枚举 Options 绑定、Configure<T>、PostConfigure<T>、BindConfiguration、自定义校验器、IValidateOptions、环境变量覆盖和 appsettings.* 分层，记录安全开关是否会在运行时被覆盖
- 对每个高风险组件记录：注册位置、保护机制、依赖配置、环境差异、前置中间件、后置中间件以及可能影响的漏洞类型

## Barrier 验证矩阵（强制）

按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 三级标准评估：

| 等级 | 检查项 | 通过标准 | 失败降级 |
|------|--------|----------|----------|
| 一级 | 中间件链存在关键顺序缺陷 | 关键安全中间件（Auth/AuthZ/CORS/Antiforgery）顺序错误或存在短路分支，导致安全控制失效 | BLOCKED → 中间件顺序正确且无短路，专项降为低优先级 |
| 二级 | 暴露面存在匿名可达高风险端点 | Swagger/HealthChecks/Hangfire/StaticFiles/SignalR/GraphQL 等端点在目标环境下匿名可达且无额外保护 | BLOCKED → 所有高风险端点均已鉴权或环境不可达 |
| 三级 | 配置覆盖导致安全开关失效 | 安全开关（HTTPS/HSTS/RateLimit/OutputCache）在运行时被环境变量/代码/分层配置覆盖关闭 | PARTIAL → 仅输出配置差异假设与验证步骤 |

## 二阶段判定流程（强制）

- **阶段 1（初筛命中）**：命中关键中间件顺序缺陷、匿名可达端点或配置覆盖点，输出 `命中ID：M{hash}`。
- **阶段 2（精筛确认）**：
  1. 逆向追踪中间件注册顺序与分支进入条件，确认安全控制是否实际失效；
  2. 验证暴露端点在目标部署环境下的真实可达性与保护机制；
  3. 对齐配置覆盖链（appsettings.json → 环境变量 → 运行时代码）的最终生效值；
  4. 若三级 Barrier 全部通过 → `确认漏洞`；任一失败 → 按矩阵降级。

## 判定规则与优先级（强制）

1. **确认漏洞**：中间件顺序缺陷导致安全控制失效 + 暴露面匿名可达 + 配置开关被覆盖关闭。输出 `确认漏洞`。
2. **待确认**：中间件/暴露面/配置证据部分存在，但部署环境或运行时行为不可证实。输出 `待确认`。
3. **误报/无风险**：中间件顺序正确、暴露面已保护、配置安全开关生效且未被覆盖。输出 `误报` 并给出判定依据。

## 测试建议与最小触发条件（强制）

- **最小触发条件**：
  - 存在 ASP.NET Core 应用（Program.cs/Startup.cs 等）
  - 中间件注册顺序存在关键安全控制（Auth/AuthZ/CORS/Antiforgery）顺序错误
  - 或存在匿名可达的高风险端点（Swagger/HealthChecks/Hangfire 等）
  - 或安全开关配置在运行时被覆盖关闭
- **测试用例建议**：
  - Happy Path：正常请求按正确中间件顺序处理，安全控制生效
  - 边界/歧义：MapWhen/UseWhen 分支短路、Development/Production 配置差异、PathBase 与反向代理前缀影响
- 每条命中输出追加 `命中ID：M{hash}` 和 `test_id：T{hash}`，用于回溯。

## 可执行参数与输出模板（强制）

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

## 输出要求

- 输出文件：framework_audit/aspnet_core_{timestamp}.md
- 必须按 中间件顺序、端点暴露面、配置绑定与安全开关、环境差异与代理边界 四个章节组织结果
- 每个问题点必须写明 代码位置、触发条件、影响范围、关联端点/功能组件、建议联动复核的漏洞专项
- 必须单列 未闭合链路与环境依赖项，说明缺失的是 配置证据、部署证据、代理证据 还是运行时注册证据

## 证据引用

- EVID_CFG_RUNTIME_SETTING_CODE
- EVID_CFG_SECURITY_SWITCH_EVIDENCE
- EVID_AUTH_TOKEN_DECODE_JUDGMENT
- EVID_AUTH_PERMISSION_CHECK_EXEC

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（中间件链确认）**：必须确认关键中间件顺序与分支进入条件。
- 🔴 **CHECKPOINT B（暴露面确认）**：必须确认匿名可达端点与环境开关生效范围。
- 🔴 **CHECKPOINT C（配置闭合确认）**：必须给出运行时最终配置值或覆盖顺序证据。
- 🛑 **STOP**：若中间件/配置证据不闭合，结论降级为 `⚠️环境依赖`。

## 失败场景与兜底（if-then）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| 中间件顺序无法闭合（分支/MapWhen/短路不清） | 补齐完整 pipeline 顺序与分支进入条件 | 结论降级 `⚠️环境依赖` 并标注缺失证据 |
| 配置覆盖链不完整（文件/环境变量/运行时代码） | 对齐最终生效值与覆盖优先级 | 仅输出待验证项，禁止“已安全”强结论 |
| 生产与开发环境边界不明 | 分环境分别给出证据与结论 | 采用最保守口径并保留复核建议 |

🔴 **STOP：任一兜底触发时，不得输出“已安全”。**

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

- 反模式：把注册代码当作运行时生效事实。正确做法：同时核对环境分支、配置覆盖与最终执行路径。
- 反模式：忽略 middleware 顺序对鉴权/限流/CORS 的影响。正确做法：必须给出顺序证据和短路分支。
- 反模式：把开发环境安全开关结论直接外推到生产。正确做法：明确 Development/Production 边界。
- 反模式：未闭合证据链就输出“已安全”。正确做法：降级为 `⚠️环境依赖` 并标注缺失证据。

输出类型映射：AUTH、CSRF、CFG、XSS、LOGIC、SESS。
