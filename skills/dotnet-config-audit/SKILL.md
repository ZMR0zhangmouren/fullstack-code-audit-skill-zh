---
name: dotnet-config-audit
description: .NET 配置安全审计工具。识别 appsettings、web.config、launchSettings、middleware 配置中的错误暴露、CORS、安全头、调试与危险开关风险。
---

# .NET 配置安全审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与 appsettings、web.config、环境变量、Options 绑定、运行时覆盖和安全开关相关的共享抓手
- 若项目存在 ConfigHelper、FeatureFlagService、TenantSettingsProvider、SecretResolver 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（用于关联受影响入口、功能面与 `route_id`）
- 可选：`auth_audit/auth_mapping_{timestamp}.md`（用于关联匿名入口、P0/P1 分桶与鉴权边界）
- 可选：`route_tracer/{route_id}/trace_{timestamp}.md` 与 `route_tracer/{route_id}/trace_summary_{timestamp}.md`（可作为配置影响到具体入口的交叉证据，不是前置硬依赖）

重点检查：

- DeveloperExceptionPage、DetailedErrors、Swagger/OpenAPI、GraphQL Playground、Hangfire Dashboard、health check、metrics 与诊断页面暴露
- CORS allow-any、AllowCredentials、Security Headers、HSTS、HTTPS 重定向、CookiePolicy、StaticFile 配置与缓存头
- appsettings.*、appsettings.{Environment}.json、web.config、launchSettings、User Secrets、环境变量、KeyVault/Secrets Manager 合并与覆盖顺序
- 反向代理、ForwardedHeaders、KnownProxies/KnownNetworks、PathBase、Host 头信任、TLS 终止与真实客户端 IP 判断边界
- DataProtection key 存储、连接字符串、日志级别、Feature Flag、实验开关、租户配置和默认账号配置
- Debug/trace/sandbox/test endpoint、文件浏览器、目录列表、静态文件映射、Razor Runtime Compilation 等危险开关
- 配置是否仅在开发环境生效，还是因环境判断错误、容器变量错配、流水线发布失误导致生产暴露

## 重点检查

- CORS 配置：AllowAnyOrigin + AllowCredentials 组合、SetIsOriginAllowed 宽松策略、通配符子域
- 错误暴露：UseDeveloperExceptionPage 在非开发环境、详细异常返回客户端、堆栈信息泄露
- 安全头缺失：X-Content-Type-Options、X-Frame-Options、CSP、HSTS、Referrer-Policy
- 危险开关：调试模式、Swagger/HealthCheck 暴露、Hangfire Dashboard 无鉴权、静态文件目录列表
- 代理信任：ForwardedHeaders 配置不当、HostFiltering 缺失、PathBase 覆盖
- 配置覆盖：环境变量覆盖安全设置、appsettings.Development.json 泄露到生产
- Kestrel 限制：请求大小、连接超时、并发限制的安全默认值

## 证据引用

- EVID_CFG_CONFIG_LOCATION
- EVID_CFG_RUNTIME_SETTING_CODE
- EVID_CFG_IMPACT_ASSOCIATION
- EVID_CFG_SECURITY_SWITCH_EVIDENCE

## 枚举规则（强制细化）

- 枚举 appsettings*.json、web.config、launchSettings、User Secrets、环境变量、KeyVault/Secret Manager、Helm/容器配置映射
- 优先搜索 UseDeveloperExceptionPage、UseSwagger、AllowAnyOrigin、ForwardedHeaders、Kestrel、DataProtection、StaticFiles、FeatureFlag 等关键配置项
- 枚举 Program.cs / Startup.cs / 扩展方法中的运行时配置覆盖、环境分支和默认值
- 对每个配置点记录：配置位置、运行时代码、影响面、环境限定条件、是否属于安全开关

## Barrier 验证矩阵（强制）

按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 三级标准评估：

| 等级 | 检查项 | 通过标准 | 失败降级 |
|------|--------|----------|----------|
| 一级 | 配置项存在且影响运行时可被修改 | appsettings/web.config/环境变量/KeyVault 中存在影响安全行为的配置项 | BLOCKED → 无安全相关配置项，专项结束 |
| 二级 | 危险配置项开启 | DeveloperExceptionPage/Swagger/AllowAnyOrigin+AllowCredentials/Hangfire Dashboard/调试开关在生产环境启用 | BLOCKED → 危险配置项均关闭或有环境限定保护，结论降级 |
| 三级 | 配置影响可达敏感端点 | CORS 过度开放/安全头缺失/代理信任不当导致敏感端点暴露或跨域利用 | PARTIAL → 仅输出潜在风险与验证步骤 |

## 二阶段判定流程（强制）

- **阶段 1（初筛命中）**：命中安全相关配置项 + 危险配置开关 + 配置影响面，输出 `命中ID：M{hash}`。
- **阶段 2（精筛确认）**：
  1. 逆向追踪 配置项 → 运行时代码 → 影响端点/组件 链路；
  2. 验证 DeveloperExceptionPage/Swagger/CORS/调试开关等危险配置是否在非开发环境启用；
  3. 评估 CORS 策略、安全头、代理信任配置对敏感端点暴露的影响；
  4. 若三级 Barrier 全部通过 → `确认漏洞`；任一失败 → 按矩阵降级。

## 判定规则与优先级（强制）

1. **确认漏洞**：安全配置项存在 + 危险配置在非开发环境启用 + 配置导致敏感端点暴露。输出 `确认漏洞`。
2. **待确认**：配置项存在但环境限定条件或运行时覆盖证据不足。输出 `待确认`。
3. **误报/无风险**：所有危险配置仅在开发环境启用且生产环境严格限制，安全头完整，CORS 严格，代理信任边界正确。输出 `误报` 并给出判定依据。

## 测试建议与最小触发条件（强制）

- **最小触发条件**：
  - 存在 appsettings/web.config/环境变量/KeyVault 等配置源
  - 危险配置项（DeveloperExceptionPage/AllowAnyOrigin/Swagger/调试开关）在非开发环境启用
  - 或 CORS/安全头/代理信任配置导致敏感端点暴露
- **测试用例建议**：
  - Happy Path：正常配置下安全控制生效，危险配置仅在开发环境启用
  - 边界/歧义：环境变量覆盖安全设置、appsettings.Development.json 泄露到生产、容器变量错配、Kestrel 请求大小限制绕过
- 每条命中输出追加 `命中ID：M{hash}` 和 `test_id：T{hash}`，用于回溯。

## 证据引用

证据引用：

- EVID_CFG_CONFIG_LOCATION
- EVID_CFG_RUNTIME_SETTING_CODE
- EVID_CFG_IMPACT_ASSOCIATION
- EVID_CFG_SECURITY_SWITCH_EVIDENCE

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（配置来源确认）**：必须同时确认配置文件、环境变量与运行时代码覆盖顺序。
- 🔴 **CHECKPOINT B（环境边界确认）**：必须区分 Development/Production 生效条件后再下结论。
- 🔴 **CHECKPOINT C（影响入口确认）**：必须给出配置项影响的入口/组件映射。
- 🛑 **STOP**：若无法确认运行时最终生效值，结论降级为 `⚠️环境依赖`，禁止输出强结论。

## 失败场景与兜底（if-then）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| 无法确认配置最终生效值 | 对齐文件、环境变量、代码覆盖优先级 | 结论降级 `⚠️环境依赖` 并列缺失来源 |
| 环境分支（Dev/Prod）证据冲突 | 分环境分别给出配置证据与影响面 | 采用最保守口径，不输出强结论 |
| 缺少配置到入口组件映射 | 补充受影响端点/组件链路 | 暂列待验证风险，禁止“无风险”结论 |

🔴 **STOP：任一兜底触发时，禁止输出“配置已安全”。**

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

- 反模式：仅看 appsettings 静态值就下结论。正确做法：同时核对环境变量与运行时覆盖。
- 反模式：混淆开发与生产配置。正确做法：逐环境标注生效条件与差异。
- 反模式：忽略代理与宿主差异。正确做法：明确 Kestrel/IIS/反代边界。
- 反模式：证据未闭合仍给强结论。正确做法：降级 `⚠️环境依赖` 并列缺失项。

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

- vuln_audit/cfg_{timestamp}.md
- 可选：vuln_poc/cfg_{timestamp}.md（如能构造复现请求或明确验证步骤）

## 机制扩展：安全配置暴露与响应信息披露（2026-09-14 台账轮）

### 机制描述与边界

本扩展覆盖两条暴露链：

- **内部信息披露链**：路由/配置请求 → 文档/配置/元数据响应 → 内部信息暴露。未授权请求者从响应中获得内部实现细节、部署配置、中间件信息。
- **secret 泄露链**：响应字段 → secret material → 凭据泄露。响应中直接携带连接字符串、私钥、access key 等凭据材料。

台账边界（逐字）：发现 secret material 优先归入 secret exposure 路径；公开且预期的 API 文档不判漏洞。

### 重点检查与枚举抓手

每命中记录：文件、行号、端点/响应点、暴露内容类型。

- **配置/元数据端点**：`IConfiguration` 全量导出/调试端点、`/swagger`（含 `Swashbuckle` 全部文档与 schema 暴露）、`/hangfire` Dashboard、`/healthchecks`（细节级健康检查暴露依赖信息）、`Web.config` / `appsettings*.json` 可被下载、IIS 目录浏览。
- **错误响应披露**：`DeveloperExceptionPage` 生产环境开启、`UseDeveloperExceptionPage` 未按环境条件化、错误响应携带堆栈/配置细节、`IncludeScopes` 将日志作用域（含内部状态）外泄、`DetailedErrors` 开启。
- **响应中的 secret 模式**：连接字符串（`Server=`/`Data Source=` 含口令）、`-----BEGIN PRIVATE KEY-----` / `-----BEGIN RSA PRIVATE KEY-----`、AKIA 形态 access key、JWT 硬编码于响应或前端配置、存储账户密钥。

### 验证矩阵

| Barrier 类型 | 验证动作 | 判定标准 |
|-------------|---------|---------|
| **端点访问控制** | 对配置/元数据端点发起未授权请求，确认是否要求认证+授权 | 未授权被拒或仅公开预期文档 → ✅ 安全；未授权可得内部信息 → 🔴 高危待确认 |
| **生产错误页收敛** | 生产配置下触发异常，确认响应为统一错误页，无堆栈/配置/作用域细节 | 统一收敛 → ✅ 安全；泄露堆栈/配置/内部路径 → 🔴 高危待确认 |
| **secret 模式扫描与响应拦截** | 扫描响应体是否命中连接字符串、私钥头、AKIA、JWT 等 secret 模式，并追踪其进入响应的路径 | 无 secret 入响应 → ✅ 安全；检出可定位来源 → 🔴 高危待确认 |
| **公开文档白名单** | 确认暴露的文档类端点是否属于产品预期公开（如对外公开 API 文档），按预期性排除 | 预期公开 → 不判漏洞；非预期公开 → ⚠️ 待确认 |

🔴 **STOP：任一 barrier 验证为 `silent-fallback` 或 `fail-open` 时，禁止将结论标记为「已确认安全」或「误报」。**

### 判定规则

确认需按路径分别闭合 EVID：

**内部信息路径**需同时闭合以下两个 EVID，缺一不可：

1. **端点暴露面闭合**：路由/配置/元数据端点未授权可访问面证据（`EVID_CFG_SENSITIVE_ENDPOINT_EXPOSURE`）。
2. **内部信息实际披露闭合**：响应实际暴露内部实现/部署配置证据，非仅端点存在（`EVID_CFG_INTERNAL_INFO_DISCLOSURE`）。

**secret 路径**以第三 ID 替代第二 ID：响应中检出 secret material 的凭据泄露证据（`EVID_CFG_SECRET_MATERIAL_IN_RESPONSE`）。

🔴 **确认阈值（台账原文）：需证明响应内容实际暴露内部信息或 secret material；仅凭端点存在或字段名疑似不得确认；公开且预期的 API 文档不判漏洞。**

### 测试建议

- **正向**：未授权访问配置/元数据端点，确认获得内部信息；扫描响应确认 secret 模式可检出。
- **负向**：认证+授权收敛、生产错误页统一、secret 入响应被拦截后，不再可利用。
- **回归**：新增元数据/诊断端点（含健康检查、调度面板、配置导出）时，复核访问控制与预期公开白名单。

### 证据引用

- `EVID_CFG_SENSITIVE_ENDPOINT_EXPOSURE`：路由/配置/元数据端点未授权可访问面证据（两路径共用第一 ID）
- `EVID_CFG_INTERNAL_INFO_DISCLOSURE`：响应实际暴露内部实现/部署配置证据（内部信息路径第二 ID）
- `EVID_CFG_SECRET_MATERIAL_IN_RESPONSE`：响应中检出 secret material 的凭据泄露证据（secret 路径替代第二 ID）
