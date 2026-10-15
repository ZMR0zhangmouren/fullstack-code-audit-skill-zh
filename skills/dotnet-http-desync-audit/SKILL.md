---
name: dotnet-http-desync-audit
description: .NET HTTP Desync/Request Smuggling 审计。识别 Content-Length 与 Transfer-Encoding 冲突、代理不一致、请求前缀截断等 HTTP 请求走私风险，输出分级、证据和修复建议。
---

# .NET HTTP Desync / Request Smuggling 审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖以下与 HTTP Desync 相关的共享抓手：
  - **入口定义抓手**：Minimal API（MapGet/MapPost/MapGroup）、MVC Controller、Middleware 管道
  - **绑定与转换抓手**：FromBody、FromForm、Request.Body、Request.ContentLength、Request.ContentType
  - **前置控制抓手**：UseRouting、UseCors、ForwardedHeaders、自定义请求处理中间件
  - **安全配置抓手**：Kestrel 配置、IIS/Nginx 反向代理配置、AddKestrel
- 若项目存在 HTTP 客户端封装（HttpClientFactory、自定义 HttpMessageHandler），必须补充到输出中的项目内抓手章节

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（用于对齐入口、参数绑定与 `route_id`）
- 可选：`framework_audit/*_{timestamp}.md`（用于补充 Kestrel 配置、反向代理中间件、请求处理管道）
- 若属于 trace-gate 专项：优先消费 `route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 若属于静态证据驱动专项：`route_tracer/*` 仅作为交叉证据，不是前置硬依赖
- 本专项属于**静态证据驱动 + 框架配置依赖**类型，核心分析基于 HTTP 请求解析配置和代理层行为

## 重点检查

### 1. Content-Length 与 Transfer-Encoding 冲突

- `Request.ContentLength` 与 `Request.Headers["Transfer-Encoding"]` 同时存在的边界行为
- ASP.NET Core Kestrel 对 CL/TE 冲突的处理策略（RFC 7230 合规性）
- 自定义 `RequestDelegate` 或中间件中手动读取 `Request.Body` 的逻辑
- `EnableRequestDelegateRewind` 与请求可重读配置

### 2. Transfer-Encoding 解析行为

- `Transfer-Encoding: chunked` 的解析入口点
- 不完整或畸形的 Chunked 编码处理
- `Transfer-Encoding` 值的大小写、空格、级联处理
- 自定义 Stream 包装器对 Chunked 数据的处理

### 3. 代理层不一致性

- `UseForwardedHeaders` 配置中的 `ForwardedHeaders.InternalProxies` 与 `ForwardedHeadersOptions`
- X-Forwarded-For、X-Forwarded-Proto、X-Forwarded-Host 的信任边界
- 代理与后端之间的协议不一致（HTTP/1.1 vs HTTP/2 或 h2c）
- Nginx/Apache/IIS 作为反向代理时的 Header 处理差异
- Load Balancer 层的 Connection Header 处理

### 4. HTTP/2 请求走私

- HTTP/2 到 HTTP/1.1 的协议降级点
- HEADERS 帧中的伪-header 注入风险
- `SO_REUSEADDR` / 连接复用导致的请求边界混淆
- HTTP/2 preface 与 HTTP/1.1 Upgrade 请求的边界

### 5. 请求前缀截断

- 请求管道中异常导致的提前终止处理
- Middleware 管道短路（`next()` 未调用）后的残留数据
- Response Start 后的请求体读取不一致
- 错误页面或重定向后的请求流状态

### 6. 响应拆分关联（Response Tail Injection）

- 响应 Header 输出点与用户输入的关联
- `Response.Headers`、`Response.Cookies` 的动态设置
- 错误响应中的请求信息回显
- 自定义错误处理中的 Header 注入

### 7. Kestrel 特定配置

- `KestrelServerOptions.AddServerHeader` 配置
- `ListenOptions.Protocols` 设置（HTTP/1.1、HTTP/2、h2c）
- `KeepAliveTimeout`、`RequestHeadersTimeout` 配置
- `Http2.MaxConcurrentStreams` 设置

## 枚举规则（强制细化）

### CL/TE 冲突枚举

搜索关键字：
- `Request.ContentLength`
- `Request.Headers["Transfer-Encoding"]`
- `Request.EnableBuffering`
- `Request.Body`
- `HttpRequest` 中的 `ReadAsync`、`ReadToEnd`、`CopyToAsync`
- `TransferCoding`, `TransferEncoding`
- `ContentLength`, `Content-Length`

枚举记录要求：
- 记录每个 `Request.ContentLength` 与 `Request.Body` 读取的组合点
- 记录 CL 值与实际 Body 长度的对比偏差情况
- 记录 `EnableRequestDelegateRewind` 配置（如果存在）
- 记录任何手动 ContentLength 验证逻辑

### 代理配置枚举

搜索关键字：
- `UseForwardedHeaders`
- `ForwardedHeadersOptions`
- `InternalProxies`
- `KnownProxies`
- `XForwardedForHeaderName`
- `XForwardedProtoHeaderName`
- `XForwardedHostHeaderName`
- `KnownNetworks`
- `KestrelServerOptions`
- `AddKestrel`
- `ConfigureKestrel`
- `IISIntegrationMiddleware`

枚举记录要求：
- 记录 `UseForwardedHeaders` 的配置完整性和信任边界
- 记录 KnownProxies / KnownNetworks 列表的覆盖范围
- 记录代理协议版本配置（HTTP/1.1、HTTP/2）
- 记录任何自定义 Header 清理逻辑

### HTTP/2 配置枚举

搜索关键字：
- `HttpProtocols`
- `Http2`
- `Http1AndHttp2`
- `HttpProtocolVersion`
- `IConnectionLifecycleFeature`
- `IHttpProtocolFeature`
- `Protocol`

枚举记录要求：
- 记录 HTTP/2 启用状态和协议版本配置
- 记录任何 HTTP/2 到 HTTP/1.1 的降级配置
- 记录 h2c（clear text HTTP/2）配置
- 记录连接复用配置

### 请求处理管道枚举

搜索关键字：
- `app.Use`
- `app.Run`
- `app.Map`
- `RequestDelegate`
- `Middleware`
- `next()`
- `await _next(context)`
- `context.Response`
- `context.Request.Body`
- `IApplicationBuilder`

枚举记录要求：
- 记录所有自定义中间件中的请求体读取操作
- 记录中间件管道顺序（特别是不调用 `next()` 的短路点）
- 记录任何在 Response Start 后继续读取请求的逻辑
- 记录异常处理中间件对请求流的影响

### 响应拆分枚举

搜索关键字：
- `Response.Headers`
- `Response.Cookies`
- `Response.AppendHeader`
- `Response.SetCookie`
- `IActionResult`
- `ContentResult`
- `RedirectResult`
- `StatusCodeContext`
- `OnStarting`
- `OnCompleted`

枚举记录要求：
- 记录动态 Header 设置点与用户输入的关联
- 记录 Cookie 中的用户输入来源
- 记录任何错误响应中的请求信息回显
- 记录 StatusCode 页面的自定义实现

## Barrier 验证矩阵（强制）

按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 三级标准评估：

| 等级 | 检查项 | 通过标准 | 失败降级 |
|------|--------|----------|----------|
| 一级 | 代理-后端解析链存在差异 | 前置代理（Nginx/IIS/ALB）与 ASP.NET Core 后端对 CL/TE/分块的解析行为不一致 | BLOCKED → 无解析差异证据，专项结束 |
| 二级 | 报文歧义可构造 | CL/TE 冲突、畸形分块、HTTP/2 降级等歧义可被实际构造并穿越代理 | BLOCKED → 结论降级为 `⚠️环境依赖` |
| 三级 | 走私请求可达敏感端点 | 走私后的请求可访问认证/支付/管理类敏感接口并产生实际副作用 | PARTIAL → 仅输出理论风险与验证步骤 |

## 二阶段判定流程（强制）

- **阶段 1（初筛命中）**：命中 CL/TE 冲突点、代理配置差异或 HTTP/2 降级配置，输出 `命中ID：M{hash}`。
- **阶段 2（精筛确认）**：
  1. 确认前置代理-后端解析链顺序与行为差异（CL/TE 优先级、分块边界处理）；
  2. 验证报文歧义是否可实际构造并穿越代理层；
  3. 评估走私请求是否可达敏感端点并产生副作用；
  4. 若三级 Barrier 全部通过 → `确认漏洞`；任一失败 → 按矩阵降级。

## 判定规则与优先级（强制）

1. **确认漏洞**：解析链差异存在 + 报文歧义可构造 + 走私可达敏感端点。输出 `确认漏洞`。
2. **待确认**：解析差异或配置证据部分存在，但代理行为或端到端可利用性不可证实。输出 `待确认`。
3. **误报/无风险**：代理与后端解析行为一致（均 RFC 7230 合规），或无可构造的歧义边界。输出 `误报` 并给出判定依据。

## 测试建议与最小触发条件（强制）

- **最小触发条件**：
  - 存在前置反向代理（Nginx/Apache/IIS/ALB）与 ASP.NET Core 后端
  - 代理与后端对 CL/TE 优先级、分块边界或 HTTP/2 降级处理不一致
  - 可构造歧义请求穿越代理并被后端解析为独立请求
- **测试用例建议**：
  - Happy Path：正常请求被正确解析，代理与后端行为一致
  - 边界/歧义：CL+TE 双头冲突、分块长度畸形、HTTP/2 伪头注入、连接复用边界混淆
- 每条命中输出追加 `命中ID：M{hash}` 和 `test_id：T{hash}`，用于回溯。

## 证据引用

## 证据引用

- EVID_DESYNC_CL_T_CONFLICT：Content-Length 与 Transfer-Encoding 冲突
- EVID_DESYNC_PROXY_INCONSISTENCY：代理层不一致性
- EVID_DESYNC_REQUEST_PREFIX_TRUNCATION：请求前缀截断
- EVID_DESYNC_HTTP2_SMUGGLING：HTTP/2 请求走私
- EVID_DESYNC_RESPONSE_TAIL_INJECTION：响应尾部注入

## 失败与降级分支（强制）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| 无法确认代理层真实配置（仅见应用代码） | 输出应用侧证据并标记缺失的代理配置文件 | 结论降级为 `⚠️环境依赖`，禁止“已确认可利用” |
| CL/TE 仅存在理论冲突，缺少可达请求路径 | 保留冲突点并补充入口映射 | 归入待验证风险池，trace_status 至少 PARTIAL |
| HTTP/2 降级链不可证实 | 记录协议配置与降级假设 | 输出“需联调验证”，不得给 P0 强结论 |
| 中间件顺序无法确定（多环境差异） | 按已知启动配置输出主路径 | 补充“环境差异分支”，结论降级 |

🔴 **STOP：存在环境关键证据缺失时，不得输出“确认可利用”措辞。**

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

| # | 反模式 | 为什么不要做 | 正确做法 |
|---|---|---|---|
| 1 | 只凭关键字命中就判定走私成立 | desync 依赖端到端解析差异 | 必须给出代理-后端不一致证据 |
| 2 | 忽略 HTTP/2/1.1 协议边界 | 协议降级决定可利用性 | 明确记录协议链与降级点 |
| 3 | 把“待验证”写成“高危已确认” | 会污染 exploit-chain 结论强度 | 使用待验证/环境依赖分级 |


## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（链路拓扑确认）**：必须确认前置代理、网关、应用服务器解析链顺序。
- 🔴 **CHECKPOINT B（报文歧义确认）**：必须确认 CL/TE、分块、复合头处理差异。
- 🔴 **CHECKPOINT C（利用后果确认）**：必须确认请求走私是否可达敏感端点。
- 🛑 **STOP**：若链路拓扑与解析差异未闭合，结论降级为 `⚠️待验证`。

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

- vuln_audit/http-desync_{timestamp}.md
- vuln_poc/http-desync_{timestamp}.md（已确认 / 待验证 / 环境依赖 PoC）

### 输出文件结构

```
vuln_audit/http-desync_{timestamp}.md
├── # HTTP Desync / Request Smuggling 审计报告
├── ## 摘要
│   ├── 发现数量
│   ├── 高危项列表
│   └── 建议优先级
├── ## CL/TE 冲突分析
│   ├── 冲突点列表（route_id + 代码位置 + 证据）
│   └── 风险评级
├── ## 代理配置分析
│   ├── 配置完整性评估
│   ├── 信任边界评估
│   └── 不一致性列表
├── ## HTTP/2 走私分析
│   ├── 协议降级点
│   └── 走私向量评估
├── ## 请求处理管道分析
│   ├── 中间件顺序图
│   └── 截断风险点
├── ## 响应拆分分析
│   ├── 动态 Header 设置点
│   └── 注入向量评估
├── ## 项目内抓手补充
│   ├── 私有封装
│   └── 特殊配置
└── ## 修复建议
    ├── Kestrel 配置优化
    ├── 代理配置加固
    └── 请求验证强化
```

### vuln_poc 结构

```
vuln_poc/http-desync_{timestamp}.md
├── # HTTP Desync PoC 模板
├── ## CL/TE 冲突 PoC
│   └── 请求模板
├── ## 代理走私 PoC
│   └── 请求模板
├── ## HTTP/2 走私 PoC
│   └── 请求模板
└── ## 验证方法
    └── 测试步骤
```