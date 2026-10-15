# .NET / Node.js Code Audit Skill

本仓库是一套面向 .NET 与 Node.js 平台的白盒代码安全审计 Skill 集合（node 家族镜像 dotnet 家族方法论，跨端层支持前后端全栈审计），dotnet 侧整体设计沿用 PHP 项目的方法论：

- 先做入口与参数建模
- 再做数据流追踪与证据闭合
- 再做分类漏洞审计
- 最后做质量汇总与利用链聚合

项目覆盖 ASP.NET Core、ASP.NET MVC、ASP.NET Web API、Blazor、SignalR、GraphQL、WCF 以及常见类库场景；Node.js 侧覆盖 Express、Koa、Fastify、Next.js、Nuxt、NestJS、GraphQL，支持前后端全栈（stack_mode=BOTH）审计。适用于合法授权前提下的源码审计、修复验证与回归分析。

> 📖 **首次部署与使用请阅读：[docs/初始化与使用指南.md](docs/初始化与使用指南.md)**（部署步骤、三种覆盖模式、断点续跑、门禁验收、回归测试方案）

## 项目特点

- 证据契约驱动：以 dotnet-route-tracer 输出的 EVID_* 证据点作为多数子审计 Skill 的硬门槛
- 路由和参数完整建模：dotnet-route-mapper 必须输出完整入口、参数结构和请求模板
- 结论强度受控：高危结论依赖 trace_status、Sink Summary 和 EVID_* 闭合
- 兼顾召回和准确率：通过静态兜底、SINK_SUSPECT 和待补证风险池抑制漏报与误报
- 兼容现代与遗留栈：覆盖 Minimal API、Attribute Routing、MVC Controller、Hub、GraphQL Endpoint、WCF Service

## 能力总览

### 基础设施

- **编排与汇总**
  - dotnet-audit-pipeline：全链路编排与质量汇总
- **前置索引**
  - dotnet-codegraph-indexer：CodeGraph 代码知识图索引管理（必选前置步骤，失败回退静态分析）
- **入口建模与追踪**
  - dotnet-route-mapper：识别 HTTP、Hub、GraphQL、WCF 等入口与参数
  - dotnet-route-tracer：追踪入口到 Sink 的分支、参数映射和证据点
- **扫描与漏洞发现**
  - dotnet-scan-audit：全量代码扫描与入口基线建立（P0 新增）
  - dotnet-vuln-scanner：扫描 NuGet 依赖漏洞并推断受影响入口（工具链：`dotnet list package --vulnerable`、osv-scanner）
- **覆盖与补检**
  - dotnet-coverage-audit：增量变更补检与覆盖率追踪（P0 新增）
- **分析与质检**
  - dotnet-briefing-agent：候选漏洞参数清单生成（P0 新增）
  - dotnet-review-agent：审计产出证据质检与一致性校验（P0 新增；含最小只读复核权的证据真实性抽检，可识别疑似编造证据）


### 漏洞专项（35 个）

#### 注入类（10个）
- SQL、NoSQL、KQL、命令、LDAP、表达式、模板、XPath、SSTI、二次注入

#### Web 安全（7个）
- XSS、DOM-XSS、SSRF、XXE、反序列化、HTTP Desync、开放重定向

#### 文件操作（5个）
- 读取、上传、写入、解压路径穿越、文件系统

#### 协议与头部（3个）
- CRLF、CSRF、会话与 Cookie

#### 配置与加密（3个）
- Config、Crypto、供应链安全

#### 业务逻辑（4个）
- Logic、Logging、认证、IDOR（IDOR 无独立磁盘 skill，由 dotnet-auth-audit 的资源归属校验 EVID_AUTH_IDOR_OWNERSHIP_CONDITION 覆盖）

#### 导出与 AI（3个）
- 非 SQL 查询注入（SOQL/OData/FetchXML）、电子表格公式注入（CSV/Excel 导出）、AI 提示注入（prompt 组装/RAG/工具调用）

#### 框架专项（9个）

- dotnet-aspnet-core-audit
- dotnet-mvc-audit
- dotnet-webapi-audit
- dotnet-blazor-audit
- dotnet-signalr-audit
- dotnet-graphql-audit
- dotnet-wcf-audit
- dotnet-grpc-audit（gRPC 微服务通信专项）
- dotnet-minimal-api-audit（.NET 6+ Minimal API 专项）

#### Node.js / 全栈家族（2026-08 P0+P1 落地）

dotnet 家族的平行扩展（路线 B：dotnet 家族零改动），node 侧镜像其方法论（证据契约、二阶段判定、fail-close Barrier、trace-gate、覆盖门禁、manifest 断点续跑），跨端层为全新增量。

##### node 基建与编排专项（10个，P3 补齐后全量）

- node-route-mapper：Node.js 路由与参数映射（适配器策略，通用 Node + Express 先行）
- node-route-tracer：Node.js 入口到 Sink 数据流追踪
- node-auth-audit：Node.js 认证鉴权审计（passport / express-jwt / jsonwebtoken / express-session / next-auth）
- node-vuln-scanner：npm 依赖漏洞扫描（lockfile CVE、typosquatting、依赖混淆、postinstall 生命周期脚本审查；外部工具建议 npm audit --json / osv-scanner）
- node-codegraph-indexer：Node.js CodeGraph 索引管理（必选前置步骤，不可用则记录原因并回退静态分析，供 node-route-mapper / node-route-tracer 调用链加速）
- node-review-agent：node 侧审计产出证据质检与一致性校验（与 dotnet-review-agent 对称，含最小只读复核权的证据真实性抽检）
- node-scan-audit：阶段 0.5 安全扫描（risks + safe_regions，只发现不判定；镜像 dotnet-scan-audit）
- node-coverage-audit：阶段 0.6 覆盖补检（gap 计算与补检循环；完成态与 dotnet-coverage-audit 对齐）
- node-briefing-agent：阶段 3.5 候选参数清单（sink 参数 checklist，含 QUERY_OBJECT / MERGE_TARGET 结构位；镜像 dotnet-briefing-agent）
- node-exploit-chain-audit：阶段 5.1 利用链聚合（原型链污染→RCE / 云元数据 SSRF / 跨端联动 / consistency 联动；镜像 dotnet-exploit-chain-audit）

##### node 漏洞专项（31个，P3 补齐 + 2026-09-14 台账轮 2 件）

- node-proto-pollution-audit（原型链污染，JS 特有，最高优先级）
- node-cmd-audit / node-ssrf-audit / node-nosql-audit
- node-file-upload-audit / node-xss-audit / node-ssti-audit / node-session-cookie-audit
- P3 补齐 21 项（2026-09-04）：node-sql-audit / node-xxe-audit / node-deser-audit / node-ldap-audit / node-expr-audit / node-xpath-audit / node-file-read-audit / node-file-write-audit / node-archive-extract-audit / node-filesystem-audit / node-csrf-audit / node-open-redirect-audit / node-crlf-audit / node-dom-xss-audit / node-second-order-audit / node-http-desync-audit / node-config-audit / node-crypto-audit / node-logic-audit / node-logging-audit / node-supply-chain-audit（均从 NODE_VULN_SKILL_TEMPLATE.md 起稿，镜像 dotnet 同名专项 node 化，证据点按 EVID_NODE_{TYPE}_* 分组）
- 2026-09-14 台账轮 2 项：node-spreadsheet-export-audit / node-ai-prompt-audit（2026-09-14 台账轮交付，镜像 dotnet 同名专项，证据点按 EVID_NODE_{TYPE}_* 分组）

##### node framework 专项（7个）

- node-express-audit / node-koa-audit / node-fastify-audit：Node.js 经典框架专项（stack_detect 检出对应框架面时触发）
- node-nextjs-audit / node-nuxt-audit / node-nestjs-audit / node-graphql-audit：全栈/装饰器框架专项（SSR 同构 / DI + Guard / GraphQL 端点）

##### 编排与跨端（3个）

- node-audit-pipeline：node 侧子流水线编排（结构镜像 dotnet-audit-pipeline 阶段 0→5.1）
- cross-stack-contract-mapper：前后端契约对账（API 契约 / 参数映射 / 覆盖门禁三桶）
- fullstack-audit-pipeline：全栈唯一总入口（阶段 0 双栈 detect → 双栈并行 → 阶段 6 跨端 → 合并报告）

##### 跨端补充（2个）

- cross-stack-taint-linker：跨端污点链拼接（前端 Source → 后端 Sink 跨进程链路）
- cross-stack-consistency-audit：两侧配置一致性审计（JWT / cookie / CORS / CSRF / 错误处理五组对账）

##### agent（2个）

- agents/node代码审计.agent.md：node 单栈编排入口（stack_mode=NODE_ONLY）
- agents/全栈代码审计.agent.md：全栈编排入口

##### shared 新增（6个）

- NODE_AUDIT_GRABBER_INDEX.md / NODE_SINK_REFERENCE.md / NODE_VULN_SKILL_TEMPLATE.md / NODE_FRAMEWORK_SKILL_TEMPLATE.md / NODE_VULN_POC_TEMPLATE.md
- FULLSTACK_FINAL_REPORT_FIXED_TEMPLATE.md（全栈最终报告固定模板单一真源）

##### Node.js / 全栈家族 skill 清单

| 类别 | Skill | 说明 |
|------|-------|------|
| node 基建（10） | node-route-mapper / node-route-tracer / node-auth-audit / node-vuln-scanner / node-codegraph-indexer / node-review-agent / node-scan-audit / node-coverage-audit / node-briefing-agent / node-exploit-chain-audit | 路由映射、数据流追踪、鉴权、依赖扫描、索引管理、证据质检、扫描/覆盖/参数清单/利用链 |
| node 漏洞专项（31） | node-proto-pollution-audit / node-cmd-audit / node-ssrf-audit / node-nosql-audit / node-file-upload-audit / node-xss-audit / node-ssti-audit / node-session-cookie-audit + P3 补齐 21 项（sql / xxe / deser / ldap / expr / xpath / file-read / file-write / archive-extract / filesystem / csrf / open-redirect / crlf / dom-xss / second-order / http-desync / config / crypto / logic / logging / supply-chain）+ 2026-09-14 台账轮 2 项（node-spreadsheet-export-audit / node-ai-prompt-audit） | P1 高价值 8 + P3 补齐 21 + 台账轮 2，与 dotnet 家族对称 |
| node framework 专项（7） | node-express-audit / node-koa-audit / node-fastify-audit / node-nestjs-audit / node-nextjs-audit / node-nuxt-audit / node-graphql-audit | stack_detect 检出对应框架面时触发 |
| node 编排（1） | node-audit-pipeline | node 侧子流水线唯一调度入口 |
| 跨端（4） | cross-stack-contract-mapper / cross-stack-taint-linker / cross-stack-consistency-audit / fullstack-audit-pipeline | 契约对账 + 污点拼接 + 配置一致性 + 全栈总入口 |
| agent（2） | node代码审计 / 全栈代码审计 | 单栈 / 全栈编排入口 |
| shared（6） | NODE_AUDIT_GRABBER_INDEX.md / NODE_SINK_REFERENCE.md / NODE_VULN_SKILL_TEMPLATE.md / NODE_FRAMEWORK_SKILL_TEMPLATE.md / NODE_VULN_POC_TEMPLATE.md / FULLSTACK_FINAL_REPORT_FIXED_TEMPLATE.md | node 规范与模板 + 全栈报告模板 |

##### 交付状态（2026-09-04 全量 ACTIVE）

- **node 家族 P3 补齐完成（2026-09-04）**：基建编排件 4 件（node-scan-audit / node-coverage-audit / node-briefing-agent / node-exploit-chain-audit）+ 漏洞专项 21 项全部交付，node-audit-pipeline 对照表 #6-10 与 #27-47 全部 ACTIVE，「未交付专项降级指令」退役；node 侧与 dotnet 侧专项覆盖对称
- 跨端层 3 件套完整：cross-stack-contract-mapper（P1）→ cross-stack-taint-linker / cross-stack-consistency-audit（P2），全栈阶段 6 跨端审计形成「契约对账 → 污点拼接 → 一致性审计」闭环
- node 框架专项 7 个全部交付（express / koa / fastify / nextjs / nuxt / nestjs / graphql），均从 NODE_FRAMEWORK_SKILL_TEMPLATE.md 起稿（十章节 + 三层结构），按 stack_detect 检出结果触发，输出落 `node/framework_audit/{framework}_{timestamp}.md`
- node-review-agent 交付（P1-7，2026-08-23）：node 侧审计产出证据质检与一致性校验（与 dotnet-review-agent 对称，含最小只读复核权的证据真实性抽检），并同步对齐 coverage-audit 完成态（commit 492f7e8 / deac83a / c57ad1d）
- node-codegraph-indexer 交付（P3-8，2026-08-23）：node 侧 CodeGraph 索引管理（必选前置步骤，不可用则记录原因并回退静态分析），node-audit-pipeline 对照表 #11 由 DEFERRED(P3) 升级为 ACTIVE（commit 31f12bf）
- EVID_NODE_CFG 分组落地（5 ID，追加于 SESS 分组后）：SECURITY_SWITCH / RUNTIME_SETTING / MIDDLEWARE_ORDER / SSR_MODE / ERR_HANDLER
- 引用状态已 ACTIVE：node-audit-pipeline 子 skill 对照表 #12-18、fullstack-audit-pipeline 阶段 6、agent 矩阵均已升级为「P2 已交付」
- 最终收尾（2026-08-23）：P2 全部交付经 final whole-branch review（rev-final-p2 ✅ / PASS-with-minors，6/6 检查项 PASS）；T2+T3 评审 2 Minor（taint-linker 消费方路径前缀、专项名表述）与 T4+T5 评审 10 Minor（证据引用双向一致等）全部修复关闭（commit 3924e47 / 6ac9416）；PARK 观察项复核 4 FIX 落地 + 6 项维持登记（commit b44b878）；全链 15 commits（072132a→3924e47），**dotnet 家族零改动**
- **Skill 登记台账机制 + 能力缺口补齐（2026-09-14）**：新增 `docs/新增Skill登记.md` 治理台账（机制归并门槛 + 四处置 + 状态机）；按台账交付 5 个新专项（dotnet-query-injection / dotnet-spreadsheet-export / dotnet-ai-prompt / node-spreadsheet-export / node-ai-prompt）；既有扩展 5 项与负向处置 6 项登记待实现/观察。
- **既有 Skill 机制扩展落地（2026-09-14 扩展轮）**：按台账交付 5 项机制扩展（账号枚举 / 审计完整性+可用性 / 签名请求重放保护 / 配置暴露+响应信息披露 / 整数溢出），覆盖 11 个既有 skill（dotnet 6 文件 + node 5 文件）尾部追加「机制扩展」章节；EVID 字典新增 30 证据点（NODE_AUTH 新分组）；全部状态封顶「已实现，待验证」。
- **设计意图采集机制（2026-09-16，方案 A）**：pipeline 双栈新增阶段 0.7（fail-open），从目标仓库 superpowers 产物（docs/superpowers、docs/design、.superpowers/sdd）提炼 `design_intent` 六节意图摘要；证据分层规则入 `AUDIT_EXECUTION_COMMON.md` §9（意图层参考禁止 EVID 引用，冲突以代码为准）；logic-audit / auth-audit 双栈首批接入（输入依赖 + 枚举规则各一条）；不新增 skill、不新增 EVID ID

## 证据契约

仓库核心共享规则见：

- shared/EVIDENCE_POINT_IDS.md
- shared/IO_PATH_CONVENTION.md
- shared/DOTNET_SINK_REFERENCE.md
- shared/DOTNET_AUDIT_GRABBER_INDEX.md
- shared/DOTNET_AUDIT_EXECUTION_STANDARD.md   # 通用执行标准（二阶段判定、fail-close、Barrier、测试要求）
- shared/DOTNET_FINAL_REPORT_FIXED_TEMPLATE.md # 最终报告固定模板
- shared/DOTNET_FRAMEWORK_SKILL_TEMPLATE.md
- shared/DOTNET_ROUTE_OUTPUT_TEMPLATES.md
- shared/DOTNET_VULN_POC_TEMPLATE.md
- shared/DOTNET_VULN_SKILL_TEMPLATE.md
- shared/SEVERITY_RATING.md

理解方式与 PHP 版本一致：

1. route-tracer 输出参数可控性矩阵、Sink 定位、Sink Summary、Trace 完整性声明、Sink Evidence Checklist
2. 各子审计 Skill 必须逐项引用对应 EVID_* 证据点
3. 缺失关键证据时，只允许输出 ⚠️待验证 或 🔍环境依赖
4. pipeline 必须保留 Trace 未闭合 / 待补证风险池，不得静默删除
5. dotnet-security-audit-skill 默认采用强制落盘模式，结构化阶段产物不应只存在于最终汇总报告里

共享抓手索引的统一要求：

1. 各漏洞专项默认引用 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为基础检索索引
2. framework 专项与 route-tracer 也要以该索引统一入口、绑定、前置控制、敏感操作、安全配置五层口径
3. 若项目存在二次封装，必须在专项输出里补充"项目内抓手"，而不是只停留在框架原生 API

## 主流水线

建议执行顺序（与 dotnet-audit-pipeline 阶段化定义一致）：

1. dotnet-codegraph-indexer（阶段 0，必选前置步骤；不可用则记录原因并回退静态分析）
2. dotnet-scan-audit（阶段 0.5，安全扫描）
3. dotnet-coverage-audit（阶段 0.6，覆盖补检）
4. dotnet-route-mapper → dotnet-auth-audit（STATIC_MAPPING）→ dotnet-vuln-scanner → framework 检测（阶段 1，侦察）
5. Source → Sink 建模（阶段 2）与全局 sink 兜底（阶段 2.5）
6. dotnet-route-tracer（阶段 3，分批追踪）
7. dotnet-briefing-agent（阶段 3.5，候选参数清单）
8. 各漏洞专项 Skill + vuln_poc（阶段 4，Sink 审计执行）
9. dotnet-review-agent（阶段 4.5，证据质检）
10. dotnet-audit-pipeline 汇总报告（阶段 5）
11. dotnet-exploit-chain-audit（阶段 5.1，利用链聚合）

`coverage_mode` 除 `FULL | SAMPLE` 外还支持 `INCREMENTAL`：基于 git diff（或用户指定的变更文件清单）圈定变更文件集并扩展受影响调用链，只对该集合执行 scan/route/trace/专项审计；会话级断点续跑状态由 `quality/manifest_{run_id}.md` 统一维护。

**全栈模式**：当审计目标为前后端全栈项目（`stack_mode=BOTH`，输入 `dotnet_source_path` + `node_source_path`）时，以 `fullstack-audit-pipeline` 为唯一总入口——阶段 0 先做 stack-detect 双栈识别，随后双栈并行执行各自子流水线（产物经 `output_path` 隔离到 `{root}/dotnet` 与 `{root}/node`，dotnet-audit-pipeline 本体零改动），阶段 6 执行跨端审计（cross-stack-contract-mapper 前后端契约对账），最后合并为全栈统一报告；报告完成态采用分栈四声明：`dotnet_api_coverage_status` / `node_api_coverage_status` / `contract_coverage_status` / `audit_surface_status`。

## Pipeline 编排说明

dotnet-audit-pipeline 现在不只是"最后汇总"，而是整个入口 Skill 的统一编排器。它需要显式消费以下结构化产物：

- route_mapping/routes_{timestamp}.md
- route_mapping/params_{timestamp}.md
- auth_audit/auth_mapping_{timestamp}.md
- cross_analysis/high_risk_routes_{timestamp}.md
- route_tracer/{route_id}/trace_{timestamp}.md
- framework_audit/{name}_{timestamp}.md
- vuln_audit/{type}_{timestamp}.md
- vuln_poc/{type}_{timestamp}.md
- vuln_report/{project}_nuget_{timestamp}.md

也就是说，pipeline 不能只看"某专项是否跑过"，而必须明确知道：

- 哪些入口已建模
- 哪些入口已 trace，trace_status 是什么
- 哪些 framework 专项已经给出框架边界结论
- 哪些漏洞专项是基于 trace / framework 证据得出的
- 哪些漏洞专项已经生成已确认 / 待验证 / 环境依赖的 PoC
- 哪些地方仍然因为运行时实现、环境配置、代理层或宿主差异而未闭合

## 结构化产物如何被消费

### route-mapper 产物

提供统一入口底图：

- 路由模板
- HTTP 方法 / Hub / GraphQL / WCF 操作类型
- 参数结构
- 绑定来源
- 请求模板

这是后续所有 Skill 的统一入口索引。
其标准输出骨架见 shared/DOTNET_ROUTE_OUTPUT_TEMPLATES.md。

### route-tracer 产物

提供统一证据链：

- 参数可控性矩阵
- Sink Summary
- Trace 完整性声明
- Sink Evidence Checklist
- Controller / ModelBinder / Filter / Middleware / DI 链路追踪结果

漏洞专项做高强度结论时，默认优先消费这些内容。
其标准输出骨架见 shared/DOTNET_ROUTE_OUTPUT_TEMPLATES.md。

### framework_audit 产物

提供统一框架边界结论：

- Middleware 顺序
- Filter / EndpointFilter / HubFilter 覆盖关系
- 鉴权策略绑定
- 序列化与模板边界
- 宿主、代理、配置开关、运行时差异

漏洞专项不应重复从零判断这些框架级事实，而应把它们当作前置证据来消费。

### vuln_audit 产物

提供分类漏洞结论：

- 已确认风险
- 待验证风险
- 环境依赖风险
- 所需的 EVID_* 证据引用
- 与 framework_audit / route_tracer 的关联关系

### vuln_poc 产物

提供专项漏洞的 PoC 或待验证 PoC：

- 关联漏洞编号
- 关联 route_id
- 最小请求模板
- 触发前提
- 预期结果
- 已确认 / 待验证 / 环境依赖 状态

其标准输出骨架见 shared/DOTNET_VULN_POC_TEMPLATE.md。

### exploit-chain 产物

负责把单点风险连接成复合利用链，特别是：

- 入口可达性
- 鉴权薄弱点
- 参数可控性
- 下游高价值 Sink
- 框架或配置造成的放大条件

## 推荐目录与产物关系

- codegraph：CodeGraph 索引状态与质量校验（阶段 0 产物）
- route_mapping：入口与参数建模
- auth_audit：鉴权静态映射与高风险入口分桶
- route_tracer/{route_id}：单入口结构化追踪
- vuln_poc：漏洞专项 PoC / 待验证 PoC 结果
- framework_audit：框架专项结果
- vuln_audit：漏洞专项结果
- cross_analysis：高风险入口、trace 批次计划、利用链聚合
- vuln_report：依赖漏洞扫描结果

## 默认落盘目录结构

本项目默认不是"只生成一份最终报告"，而是"先真实创建结构化产物，再汇总"。

默认执行 dotnet-audit-pipeline 后，应至少落出以下目录：

- codegraph/
- scan_audit/
- coverage_audit/
- route_mapping/
- auth_audit/
- route_tracer/
- briefing/
- vuln_audit/
- vuln_poc/
- framework_audit/
- cross_analysis/
- vuln_report/
- exploit_chain/
- global_sink_fallback/
- review/
- quality/

如果某一阶段没有明确结果，也不应缺目录；应创建目录并用文件说明无结果或待验证原因。

默认还应为各阶段写入索引文件，例如：

- scan_audit/index_{timestamp}.md
- coverage_audit/index_{timestamp}.md
- route_mapping/index_{timestamp}.md
- auth_audit/index_{timestamp}.md
- route_tracer/index_{timestamp}.md
- briefing/index_{timestamp}.md
- vuln_audit/index_{timestamp}.md
- vuln_poc/index_{timestamp}.md
- framework_audit/index_{timestamp}.md
- cross_analysis/index_{timestamp}.md
- review/index_{timestamp}.md
- vuln_report/index_{timestamp}.md
- quality/pipeline_execution_{timestamp}.md

如果某阶段没有形成正式发现，也必须至少满足以下之一：

- 在对应的 index_{timestamp}.md 中直接写明无结果原因
- 额外写入 empty_result_{timestamp}.md，说明未执行、仅初筛、证据不足、环境依赖或不适用原因

## dotnet-audit-pipeline 统一协调规则

- route_tracer 是多数高强度漏洞结论的主证据来源
- framework_audit 是框架边界、运行时控制面和部署差异的主证据来源
- vuln_poc 是 vuln_audit 的默认配套产物，不再视为可有可无的附属输出
- 二者冲突时，pipeline 必须保留冲突，不得静默覆盖
- 没有 trace 时，framework_audit 可以先给出框架级风险提示，但高强度漏洞结论仍受 trace gate 约束
- 各漏洞专项必须显式说明是否消费了 framework_audit 与 route_tracer 产物；未消费就必须说明原因

如果某专项没有形成"已确认 PoC"，也必须生成 待验证 或 环境依赖 的 PoC 文件，而不是省略 vuln_poc 目录。

## 漏洞专项执行状态说明

为了让执行过程可审计、可追责，所有 dotnet-*-audit 漏洞专项都应被记录为以下状态之一：

- NOT_RUN：未执行
- INITIAL_SCREENED：只做了抓手枚举、关键字扫描、入口粗筛
- PARTIAL：已进入专项分析，但尚未完成证据闭合
- COMPLETED：已完成专项分析并形成正式输出
- NOT_APPLICABLE：当前项目或当前入口不适用

这意味着"其他漏洞类型"即使不是本轮重点，也不能静默消失；至少要在最终汇总里标记为 INITIAL_SCREENED 或 PARTIAL，而不是没有记录。

## Skill 必要章节（验收标准）

每个 `dotnet-*-audit` SKILL.md 必须包含：

1. `## 共享抓手索引引用` — 声明与 shared 索引的关系
2. `## 输入依赖` — 明确 source_path、route_mapping、route_tracer 等依赖
3. `## 重点检查` — 该专项的核心检查项
4. `## 枚举规则（强制细化）` — 具体搜索关键字与记录要求
5. `## Barrier 验证矩阵（强制）` — 专项特定的 barrier 类型、验证动作与判定标准
6. `## 二阶段判定（强制）` — 引用 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程
7. `## 判定规则（强制细化）` — 确认漏洞 / 待确认 / 误报 的专项特定条件
8. `## 测试建议（强制）` — 正向/负向/回归测试覆盖要求
9. `## 证据引用` — 引用的 EVID_* 证据点
10. `## 输出` — 产物路径与格式要求

> 新增/更新 Skill 时，漏洞专项从 `DOTNET_VULN_SKILL_TEMPLATE.md` 起稿，框架专项从 `DOTNET_FRAMEWORK_SKILL_TEMPLATE.md` 起稿，确保 Barrier 验证矩阵、二阶段判定、命中 ID 与 test_id 已纳入模板。

## 输入与输出

### 输入

- source_path：.NET 项目或解决方案根目录
- output_path：输出目录，可选，默认 {source_path}_audit

### 输出

合并模式下通常输出：

- {output_path}/{project_name}_dotnet_audit_{timestamp}.md

独立运行模式下，各 Skill 可在建议目录结构中落盘独立文件，逻辑名与合并报告章节等价。

最终合并报告至少应包含：

- 执行清单
- Skill 使用与发现矩阵
- 入口覆盖矩阵
- Trace 覆盖矩阵
- Framework 覆盖矩阵
- Vulnerability 覆盖矩阵
- PoC 覆盖矩阵
- 证据冲突与待复核项
- 风险统计与利用链
- Trace 未闭合 / 待补证风险池

其中 Skill 使用与发现矩阵建议至少包含：

- skill_name
- skill_type
- execution_status
- findings_status
- primary_outputs
- depends_on
- notes

这样在一次完整执行后，可以直接看出：

- 哪些 dotnet-*-audit skills 被实际调用了
- 哪些只做了初步筛选
- 哪些做了一半卡在 trace 或环境证据上
- 哪些已经确认发现问题
- 哪些没有发现问题但已完整执行

## 适用场景

- ASP.NET Core Web 项目上线前审计
- 老旧 .NET Framework / WCF 项目白盒回归
- 依赖升级后的修复验证
- 框架配置与中间件顺序检查
- 鉴权、序列化、文件与表达式高风险点专项复核

## 目录结构

- dotnet-audit-pipeline：总编排
- dotnet-route-mapper / dotnet-route-tracer：入口建模与追踪
- dotnet-*-audit：分类审计与框架专项
- shared：证据、路径、Sink 与分级规范

当前默认的物理产出目录包括：

- route_mapping
- auth_audit
- route_tracer
- vuln_audit
- vuln_poc
- framework_audit
- cross_analysis
- vuln_report
- quality

## 后续如何扩展新 Skill 与产物模板

本项目支持继续扩展新的漏洞专项，但扩展方式必须遵循当前这套统一方法论，不能只新增一个名称和若干检查点就结束。

### 1. 什么时候需要新增一个漏洞专项 Skill

满足以下任一条件时，建议新增独立 Skill，而不是塞进已有专项：

- 风险类型拥有独立的敏感操作模型或 Sink 模型
- 风险判断依赖独特的框架机制、运行时语义或配置面
- 现有专项无法清晰承载其枚举规则、证据引用和输出要求
- 审计结果需要单独统计、单独分级、单独进入 exploit chain 聚合

例如：如果后续要补 Message Queue、反向代理信任边界、缓存投毒、SSTI 变体、反射调用滥用、对象映射污染等类型，通常应考虑作为新 Skill 单独建设。

### 2. 新 Skill 的命名规则

- 漏洞专项统一命名为 dotnet-{type}-audit
- framework 专项统一命名为 dotnet-{framework}-audit
- 名称必须直接反映专项职责，避免使用过于泛化的 custom、misc、security 之类命名

建议示例：

- dotnet-cache-poisoning-audit
- dotnet-message-queue-audit
- dotnet-reflection-abuse-audit

对于 framework 专项，建议参考 shared/DOTNET_FRAMEWORK_SKILL_TEMPLATE.md；对于漏洞专项，建议参考 shared/DOTNET_VULN_SKILL_TEMPLATE.md。

### 3. 新漏洞专项 Skill 的最小结构

每个新增漏洞专项至少应包含以下结构：

- YAML frontmatter：name、description
- 共享抓手索引引用
- 重点检查
- 枚举规则（强制细化）
- 证据引用
- 输出要求或输出文件

也就是说，新专项必须和当前成熟专项保持一致，不能退回到只有"重点检查"的粗粒度文档。

如果新增的是 framework 专项，则同样应保持三层结构，但输出路径应落在 framework_audit/{framework}_{timestamp}.md，并显式说明其与 route_tracer、vuln_audit、pipeline 的消费关系。

### 4. 必须接入 shared 的哪些规范

新增 Skill 时，默认必须引用以下 shared 文档：

- shared/DOTNET_AUDIT_GRABBER_INDEX.md
- shared/EVIDENCE_POINT_IDS.md
- shared/IO_PATH_CONVENTION.md
- shared/SEVERITY_RATING.md
- shared/DOTNET_SINK_REFERENCE.md
- shared/DOTNET_AUDIT_EXECUTION_STANDARD.md
- shared/DOTNET_VULN_POC_TEMPLATE.md

其中职责分别是：

- 抓手索引：统一搜索关键字、优先枚举对象和记录字段
- 证据 ID：统一结论引用口径
- IO 约定：统一逻辑章节名和物理落盘路径
- 分级规则：统一风险强度与措辞边界
- Sink 参考：统一敏感操作模型
- 执行标准：统一二阶段判定、fail-close Barrier、命中 ID 与测试要求

如果新漏洞类型无法被现有 shared 规则充分表达，应先补 shared，再补新 Skill，而不是让单个 Skill 私自定义一套新规范。

### 5. 如何编写"重点检查"

重点检查负责定义这个漏洞类型最值得优先看的风险面。编写时应覆盖：

- 典型 .NET 原生 API 或框架入口
- 常见二次封装位置
- 影响风险成立的上下文条件
- 与认证、授权、配置、宿主环境有关的放大因素

重点检查不应写成空泛概念列表，而应尽量直接点出：

- 哪些类
- 哪些方法
- 哪些特性或配置
- 哪些常见业务场景

### 6. 如何编写"枚举规则（强制细化）"

枚举规则是 Skill 的执行层核心。每条规则应尽量回答以下问题：

- 先搜什么关键字
- 再枚举什么对象
- 对每个命中点要记录什么字段
- 二次封装出现时如何补充项目内抓手
- 哪些情况需要继续向 route_tracer 或 framework_audit 追证

推荐写法：

- 优先搜索哪些 API / 特性 / 注册点
- 枚举哪些入口、哪些服务、哪些包装层
- 记录哪些输入源、分支条件、保护逻辑、最终执行点
- 对每个命中点记录 代码位置、调用链位置、可控参数、保护措施、关联入口

### 7. 如何定义新的证据点

如果新漏洞类型需要新的 EVID_* 证据点，应同步更新 shared/EVIDENCE_POINT_IDS.md。

新增证据点时应遵循：

- 命名清晰稳定，直接体现证据语义
- 尽量描述"事实证据"，而不是"结论标签"
- 能被 route_tracer、framework_audit 或专项静态分析结果稳定引用

例如，不要只写 EVID_HIGH_RISK；应写成更具体的：

- EVID_CACHE_KEY_USER_CONTROLLED
- EVID_PROXY_TRUST_HEADER_OVERRIDE
- EVID_REFLECTION_TARGET_USER_CONTROLLED

### 8. 如何接入 dotnet-audit-pipeline

新增漏洞专项后，必须同步考虑 pipeline 接入，而不是只创建一个孤立 Skill。

至少要明确四件事：

- 这个专项主要消费哪些输入产物
- 它是否依赖 route_tracer 的结构化 trace
- 它是否依赖 framework_audit 的框架边界结论
- 它最终输出到哪个 vuln_audit/{type}_{timestamp}.md

如果某专项高度依赖框架边界，例如缓存、代理、序列化、模板、认证上下文，就必须显式声明对 framework_audit 的消费关系。

如果某专项高度依赖参数可控性、调用链和最终执行点，就必须显式声明对 route_tracer 的消费关系。

如果新增的是 route mapping 或 trace 相关能力，除 Skill 自身规则外，还必须保持与 shared/DOTNET_ROUTE_OUTPUT_TEMPLATES.md 一致的输出骨架，避免破坏 pipeline 和下游专项的结构化消费。

### 9. 如何判断该扩展是合格的

新增 Skill 至少应满足以下验收标准：

- 名称、description、职责边界清晰
- 已引用 shared 抓手索引和其他必要 shared 规则
- 已具备三层结构：重点检查 + 枚举规则 + 输出要求
- 已说明证据引用口径
- 已说明与 route_tracer / framework_audit / pipeline 的关系
- 输出路径符合 shared/IO_PATH_CONVENTION.md
- 能与现有专项区分边界，不产生大面积重复职责

### 10. 推荐扩展流程

推荐按下面顺序扩展：

1. 先定义新漏洞类型的职责边界
2. 确认是否需要新增 shared 抓手、Sink 或 EVID 规则
3. 创建 dotnet-{type}-audit/SKILL.md
4. 补齐三层结构与证据引用
5. 说明其消费哪些 route_tracer / framework_audit 产物
6. 在 README 中补入能力总览或扩展说明
7. 最后做全目录校验

### 11. 共享模板文件

新增漏洞专项时，优先直接使用 shared/DOTNET_VULN_SKILL_TEMPLATE.md 作为起稿模板，而不是在 README 中复制粘贴旧片段。

新增 framework 专项时，优先使用 shared/DOTNET_FRAMEWORK_SKILL_TEMPLATE.md。

需要统一 route-mapper / route-tracer 产物格式时，优先使用 shared/DOTNET_ROUTE_OUTPUT_TEMPLATES.md，而不是在各 Skill 中重复维护一套格式样例。

使用方式：

- 先复制 shared/DOTNET_VULN_SKILL_TEMPLATE.md 的模板主体
- 如果是 framework 专项，则复制 shared/DOTNET_FRAMEWORK_SKILL_TEMPLATE.md 的模板主体
- 将 {type} 替换为具体漏洞类型
- 再按专项特性补齐 重点检查、枚举规则（强制细化）、证据引用、输出要求
- 如需扩展 shared 抓手、Sink 或 EVID，先更新 shared 文档，再更新新 Skill

route-mapper / route-tracer 的产物模板使用方式：

- routes_{timestamp}.md、params_{timestamp}.md、quality/route_mapper_validation_{timestamp}.md 参照 shared/DOTNET_ROUTE_OUTPUT_TEMPLATES.md 中的 route-mapper 模板
- trace_{timestamp}.md、trace_summary_{timestamp}.md 参照 shared/DOTNET_ROUTE_OUTPUT_TEMPLATES.md 中的 route-tracer 模板
- 如需追加字段，只能在保持核心章节和关键字段不变的前提下追加

如果你后续继续扩展这个项目，建议始终把"shared 统一口径 + route_tracer 证据链 + framework_audit 边界结论 + pipeline 显式消费"作为新增 Skill 的四个固定约束。

## 2026年5月覆盖优化更新

### 新增漏洞专项（6个）- 已创建 ✅

| 专项名称 | 优先级 | 说明 |
|----------|--------|------|
| dotnet-xpath-audit | P2 | XPath 注入审计，从 XXE 拆分 |
| dotnet-supply-chain-audit | P0 | 供应链安全审计，OWASP A08 |
| dotnet-ssti-audit | P1 | Server-Side Template Injection 审计，从 tpl 拆分 |
| dotnet-dom-xss-audit | P2 | DOM-XSS 审计，从 xss 拆分 |
| dotnet-http-desync-audit | P2 | HTTP Desync/Request Smuggling 审计 |
| dotnet-second-order-audit | P2 | 二次注入审计 |

### 新增框架专项（2个）- 已创建 ✅

| 专项名称 | 优先级 | 说明 |
|----------|--------|------|
| dotnet-grpc-audit | P1 | gRPC 微服务通信安全审计 |
| dotnet-minimal-api-audit | P0 | Minimal API 安全审计，.NET 6+ 核心 |

### 现有专项增强（8个）

| 专项 | 增强内容 | 优先级 |
|------|----------|--------|
| dotnet-blazor-audit | .NET 8 预渲染安全、Blazor United | P2 |
| dotnet-signalr-audit | 流式消息、Backplane 安全 | P2 |
| dotnet-graphql-audit | 字段级授权、DataLoader 安全 | P2 |
| dotnet-sql-audit | 二次注入、WAF 绕过检测 | P2 |
| dotnet-xss-audit | DOM-XSS 入口、CSP 绕过 | P2 |
| dotnet-cmd-audit | Linux/Windows 差异、编码绕过 | P2 |
| dotnet-ssrf-audit | Gopher 协议、DNS 重绑定 | P2 |
| dotnet-aspnet-core-audit | AOT 编译、Source Generator | P3 |

### 覆盖统计

- **漏洞专项**：32 个
- **框架专项**：9 个

## 本次增强内容

### 2026-06 覆盖门禁增强（pipeline 口径收敛）

为避免"专项矩阵已完成"被误读为"活动 API 已全量覆盖"，本轮新增并强化以下约束：

1. 新增 `coverage_mode: FULL | SAMPLE`（默认 FULL）
2. 新增 `route_mapping/controller_inventory_{timestamp}.md` 作为 route mapping 前置对账产物
3. 新增 `quality/api_coverage_gate_{timestamp}.md` 作为 API 覆盖门禁产物
4. 明确 `pipeline_execution` 与 `api_coverage_status` 绑定：
	- `api_coverage_status != COMPLETE` 时，禁止 `pipeline_execution = COMPLETED`
5. 明确双完成态：
	- `audit_surface_status`（专项覆盖）
	- `api_coverage_status`（入口覆盖）
6. 明确 high risk routes 双产物：
	- 全量：`cross_analysis/high_risk_routes_{timestamp}.md`
	- 样本：`cross_analysis/sampled_high_risk_routes_{timestamp}.md`

其中 sampled 产物必须在文件头显式声明：

- `coverage_mode`
- `api_coverage_status`
- `controller_coverage_percent`
- `auth_coverage_percent`
- `disclaimer`（仅代表已映射入口候选，不代表全量活动 API）

以上约束已同步到：

- `skills/dotnet-audit-pipeline/SKILL.md`
- `skills/shared/IO_PATH_CONVENTION.md`
- `skills/shared/DOTNET_ROUTE_OUTPUT_TEMPLATES.md`

本轮对 .NET Skill 库做了九类结构化增强（详见 `docs/memory/CHANGELOG_AND_DECISIONS.md`）：

1. framework 专项全部升级为与漏洞专项一致的三层结构
2. dotnet-route-tracer 升级为执行级链路追踪规范
3. shared 新增统一抓手索引，约束各 Skill 的检索与枚举口径
4. 各漏洞专项已统一显式引用 shared 抓手索引
5. dotnet-audit-pipeline 已补强为真正的统一编排入口，显式消费 route_tracer 与 framework_audit 结构化产物
6. 新增 shared 漏洞专项模板文件，统一后续 Skill 扩展起稿方式
7. 新增 shared framework 专项模板文件，统一框架 Skill 扩展起稿方式
8. 新增 shared route / trace 输出模板文件，统一 route mapping 与 trace 产物格式
9. 增加 pipeline 强制落盘模式，并将 vuln_poc 正式纳入 shared 与 pipeline 输出体系

### 2026-06 覆盖门禁第二阶段补强（模板与示例固化）

在覆盖门禁基础上，本轮继续补齐"执行模板"和"最小示例"，减少口径漂移：

1. 在 `skills/dotnet-audit-pipeline/SKILL.md` 固化最终报告片段：
	- 强制双完成态：`audit_surface_status` + `api_coverage_status`
	- 强制 coverage gate 摘要字段：`api_coverage_percent`、`pipeline_execution`、`gate_decision`
	- 强制覆盖口径声明（SAMPLE/PARTIAL 时必须声明"非全量结论"）
2. 新增轻量执行校验清单（收尾必过），建议落盘：
	- `quality/quick_validation_{timestamp}.md`
3. 在 `skills/shared/DOTNET_ROUTE_OUTPUT_TEMPLATES.md` 新增"最小示例产物包"：
	- `route_mapping/controller_inventory_{timestamp}.md`
	- `quality/api_coverage_gate_{timestamp}.md`
	- `cross_analysis/sampled_high_risk_routes_{timestamp}.md`

4. 将 `quality/quick_validation_{timestamp}.md` 标准化：
	- 在 shared 模板中新增 quick validation 骨架与判定规则
	- 在 `IO_PATH_CONVENTION` 中新增路径约定
	- 在 pipeline 中明确引用 shared 模板，禁止收尾校验格式漂移

5. 绑定 `coverage_mode` 与 `trace_batch_plan` 阈值：
	- FULL：`trace_batch_max_size` 允许 10–30（默认 10）
	- SAMPLE：`trace_batch_max_size` 允许 5–10（默认 8，禁止超过 10）
	- 超阈值计划必须判定无效并回退重排

6. 利用链报告透传覆盖口径（exploit-chain）：
	- `exploit_chain/exploit_chains_{timestamp}.md` 必须带 `coverage_mode`、`api_coverage_status`、`api_coverage_percent`
	- 当 `coverage_mode=SAMPLE` 或 `api_coverage_status=PARTIAL` 时，链路结论必须显式声明"仅覆盖已映射入口样本范围"
	- 链路总览表新增 `sampled_scope` 字段，避免将样本链路误读为全量链路

7. 新增 `quick_validation_example` 最小示例：
	- shared 模板新增：`quality/quick_validation_example_{timestamp}.md`
	- 用于培训与回归对照，不替代正式 `quick_validation_{timestamp}.md`
	- 统一示例字段：上下文、校验清单、最终判定（PASS/BLOCKED）

8. SAMPLE 模式新增批次数上限（batch_count_upper_bound）：
	- 在 `trace_batch_plan_{timestamp}.md` 中新增 `batch_count_upper_bound` 与 `planned_batch_count`
	- 当 `coverage_mode=SAMPLE` 时，强制 `planned_batch_count <= 6`
	- 超限计划必须判定无效并回退重排（优先按模块合并路由，减少碎片化批次）

9. 最终报告新增 exploit-chain 覆盖口径摘要（固定片段）：
	- 在最终报告固定模板中新增 `exploit-chain 覆盖口径摘要` 区块
	- 固定字段：`exploit_chain_coverage_mode`、`exploit_chain_api_coverage_status`、`exploit_chain_api_coverage_percent`、`exploit_chain_sampled_scope`
	- `quick_validation_{timestamp}.md` 与 `quick_validation_example_{timestamp}.md` 同步增加该区块的一致性校验项

10. 新增 `coverage_consistency_check` 跨产物一致性核对：
	- 新增建议产物：`quality/coverage_consistency_check_{timestamp}.md`
	- 用于统一核对 `api_coverage_gate`、`trace_batch_plan`、`exploit_chains`、最终报告的关键字段一致性
	- 冲突判定规则：若关键字段冲突影响结论语义，`final_status` 必须为 `BLOCKED`，并输出"冲突字段 + 来源文件 + 修复建议"
11. `quick_validation` 模板增强与 FULL 软约束：
	- `quick_validation_{timestamp}.md` 新增"字段冲突定位"小节，直接承接 `consistency_check` 结果
	- 若 `consistency_check_status=BLOCKED`，`final_decision` 联动为 `BLOCKED`
	- 最终报告固定模板新增 `4.5) 一致性核对摘要`，字段：`consistency_check_source`、`consistency_check_status`
	- FULL 模式增加批次数软提醒阈值：若 `planned_batch_count > 20`，建议评估合并（不强制回退）

12. `exploit_chain` 输出新增 consistency_check 联动：
	- `dotnet-exploit-chain-audit` 可选读取 `quality/coverage_consistency_check_{timestamp}.md`
	- 当 `final_status=BLOCKED` 时，链路"可行性"不得标记为"确认可行"，需降级并附冲突引用
	- 链路总览表新增 `consistency_check_status` 字段，链路详情新增一致性联动区块

13. 最终报告新增 exploit_chain 一致性汇总计数：
	- 固定模板 `4.5) 一致性核对摘要` 增加 `exploit_chain_consistency_check_counts`
	- 当存在 consistency_check 时，需核对 PASS/BLOCKED/N/A 计数与 exploit_chain 总览表一致
	- `IO_PATH_CONVENTION` 同步增加 exploit_chain 产物映射与 BLOCKED 语义约束

14. 补齐最小示例与计数统计口径：
	- `DOTNET_ROUTE_OUTPUT_TEMPLATES.md` 新增"最终报告固定片段最小示例（含 consistency 汇总计数）"
	- `dotnet-exploit-chain-audit` 新增 `consistency_check_counts` 统计示例行（PASS/BLOCKED/N/A）
	- 执行时建议直接复用示例，减少最终报告字段遗漏与手工统计偏差

15. 收尾双保险流程图（执行顺序可视化）：
	- 将 `coverage_gate -> consistency_check -> quick_validation -> exploit_chain/final_report` 固化为统一流程
	- 明确阻断语义：`consistency_check_status=BLOCKED` 时，不得进入"确认可行"结论
	- 用于新人接手与交付前走查，减少步骤遗漏

16. 新增 quick_validation 失败反例（计数对账失败）：
	- 在 `DOTNET_ROUTE_OUTPUT_TEMPLATES.md` 增加 `Quick Validation Example (Blocked)`
	- 典型失败：`exploit_chain_consistency_check_counts` 与 exploit_chain 总览表不一致
	- 结论要求：`consistency_check_status=BLOCKED` 时，`final_decision` 必须为 `BLOCKED`

17. 抽离最终报告固定模板 + pipeline 流程锚点：
	- 新增 `skills/shared/DOTNET_FINAL_REPORT_FIXED_TEMPLATE.md` 作为最终报告质量章节单一真源
	- `DOTNET_ROUTE_OUTPUT_TEMPLATES.md` 与 `dotnet-audit-pipeline/SKILL.md` 改为引用该模板，避免多处维护漂移
	- pipeline 新增"收尾双保险流程锚点（执行跳转）"，按 `api_coverage_gate -> consistency_check -> quick_validation -> exploit_chain -> final_report` 顺序执行

18. exploit-chain 新增 BLOCKED 计数异常自动降级措辞模板：
	- 在 `dotnet-exploit-chain-audit/SKILL.md` 增加"第七步：BLOCKED 计数异常自动降级措辞模板（强制）"
	- 触发条件：`consistency_check_status=BLOCKED` 或 `exploit_chain_consistency_check_counts` 对账失败
	- 强制动作：链路可行性降级为"推断可行/理论可行"，并补充修复动作与来源文件引用

19. 新增未映射入口独立产物 + 循环补图模板：
	- `api_coverage_status=PARTIAL` 时强制输出 `quality/unmapped_routes_{timestamp}.md`
	- 新增 `quality/route_mapping_backfill_loop_{timestamp}.md` 模板（建议），记录补图轮次与收敛过程
	- pipeline 明确：未映射活动控制器/入口未清零且未获用户显式终止前，不得结束 route mapping 阶段

20. 最终报告固定模板新增 BLOCKED 最小示例：
	- 在 `skills/shared/DOTNET_FINAL_REPORT_FIXED_TEMPLATE.md` 新增"BLOCKED 最小示例（计数对账失败）"
	- 用于训练执行人识别"最终报告字段齐全但 consistency 计数仍不可交付"的场景
	- 明确：`consistency_check_status=BLOCKED` 或计数不一致时，最终报告必须先修复后再重跑 `quick_validation`

21. exploit-chain 增加"计数修复后标准重跑顺序"：
	- 在 `dotnet-exploit-chain-audit/SKILL.md` 新增 `final_report -> consistency_check -> quick_validation -> exploit_chain` 重跑顺序
	- 目的：避免只修一处计数，遗漏联动产物与措辞恢复

22. pipeline 新增"收尾锚点检查清单"模板：
	- 新增建议产物：`quality/final_anchor_checklist_{timestamp}.md`
	- 用于逐文件勾选 `api_coverage_gate / consistency_check / quick_validation / exploit_chain / final_report`
	- 新增 PASS/BLOCKED/PENDING 汇总区块，便于一眼判断收尾状态

23. shared 新增 exploit-chain BLOCKED 失败反例：
	- 在 `DOTNET_ROUTE_OUTPUT_TEMPLATES.md` 新增 `Exploit Chains Example (Blocked)`
	- 用于训练执行人识别"利用链文件本身也需降级措辞"的场景

24. 最终报告固定模板新增"收尾锚点检查结果引用"：
	- 在 `skills/shared/DOTNET_FINAL_REPORT_FIXED_TEMPLATE.md` 新增 `4.6) 收尾锚点检查结果引用`
	- 用于回写 `final_anchor_checklist_{timestamp}.md` 的 `final_anchor_decision` 与 PASS/BLOCKED/PENDING 计数

25. shared 新增 `unmapped_routes` 的 BLOCKED 反例：
	- 在 `DOTNET_ROUTE_OUTPUT_TEMPLATES.md` 新增 `Unmapped Routes Backlog (Blocked)`
	- 用于训练执行人识别"入口覆盖未补完时必须阻断交付"的场景

26. `final_anchor_checklist` 新增 BLOCKED 来源文件摘要：
	- 在 pipeline 模板中新增 `BLOCKED 来源文件摘要` 小节
	- 用于快速定位究竟是哪个锚点文件把交付状态挡住了

27. `IO_PATH_CONVENTION` 补齐 final anchor 回写映射：
	- 新增 `quality/final_anchor_checklist_{timestamp}.md` 路径映射
	- 新增"最终报告固定字段回写来源"表，明确 `final_anchor_checklist_source`、`final_anchor_decision`、`final_anchor_checklist_counts` 的单一来源
	- 新增约束：若 `final_anchor_decision=BLOCKED`，最终报告不得使用"可交付/已通过"类正向收尾措辞

28. shared 新增 `final_anchor_checklist` PASS/BLOCKED 最小示例：
	- 在 `DOTNET_ROUTE_OUTPUT_TEMPLATES.md` 新增 `quality/final_anchor_checklist_{timestamp}.md` 的正反示例
	- 明确 `checklist_blocked_count > 0 => final_anchor_decision=BLOCKED`
	- 明确 `final_anchor_decision=BLOCKED` 时最终报告不得写"可交付/已通过/收尾完成"
29. `DOTNET_FINAL_REPORT_FIXED_TEMPLATE` 新增 `unmapped_routes_source` 字段：
	- 在固定骨架模板 `2) 覆盖门禁摘要` 新增字段：`unmapped_routes_source`
	- 验收约束：`api_coverage_status=PARTIAL` 时不得为 N/A，必须指向实际产物
	- PASS/BLOCKED 两个示例均同步填入实际路径

30. `IO_PATH_CONVENTION` 新增 `final_anchor ↔ final_report 4.6` 最小对账示例：
	- 增加 checklist 汇总区块与最终报告 4.6 字段的三字段映射关系表
	- 明确典型对账失败反例，防止"一处改了另一处漏改"
```mermaid
flowchart TD
	A[quality/api_coverage_gate_{timestamp}.md] --> B[quality/coverage_consistency_check_{timestamp}.md]
	B -->|PASS| C[quality/quick_validation_{timestamp}.md]
	B -->|BLOCKED| D[修复冲突并回写相关产物]
	D --> B
	C --> E[exploit_chain/exploit_chains_{timestamp}.md]
	E --> F[{project_name}_代码审计_{timestamp}.md]
	B --> G[consistency_check_status]
	G --> C
	G --> E
	E --> H[exploit_chain_consistency_check_counts]
	H --> F
```
该示例包用于回归对齐：执行人可直接对照字段、状态和值域检查是否符合门禁语义。

### 1. framework 专项补齐三层结构

以下 framework Skill 已统一补成 重点检查 + 枚举规则（强制细化） + 输出要求：

- dotnet-aspnet-core-audit
- dotnet-mvc-audit
- dotnet-webapi-audit
- dotnet-blazor-audit
- dotnet-signalr-audit
- dotnet-graphql-audit
- dotnet-wcf-audit

这次补齐后，framework 专项不再只是"提醒你看哪些点"，而是明确要求：

- 应该搜索哪些 .NET API、特性、注册点、过滤器或中间件
- 每条发现至少要记录哪些字段
- 框架报告应该按什么章节输出，避免只写散点结论

### 2. dotnet-route-tracer 细化为执行级规范

dotnet-route-tracer 现在要求对下列链路做显式追踪，而不是停留在"入口到 Sink"的抽象描述：

- Controller / Action 元数据
- ModelBinder / ValueProvider / JsonConverter / BindAsync 等绑定转换层
- Filter / EndpointFilter / HubFilter / MessageInspector 等前置控制层
- Middleware / branch pipeline / Route Group 元数据叠加
- DI 接口到实现类、装饰器、工厂、代理、typed client 的解析链

同时补充了：

- CRITICAL 规则
- 核心追踪范围
- Controller / Binder / Filter / Middleware / DI 五类细则
- 输出模板约束
- 更明确的 Trace 完整性声明要求

这使 route-tracer 与 dotnet-route-mapper 的详细度更接近，能更稳定地给后续漏洞专项提供可复用证据。

### 3. shared 新增 .NET 审计抓手索引

新增文件：shared/DOTNET_AUDIT_GRABBER_INDEX.md

作用：

- 统一入口定义、绑定转换、前置控制、敏感操作、安全配置五大层的搜索关键字
- 统一每类枚举时至少要记录的字段
- 统一对项目内二次封装的补充方式

这样后续继续细化 Skill 时，不需要每个文件都从零定义搜索抓手，而是可以共享同一套基础索引，再叠加专项差异。

### 4. 各漏洞专项统一引用 shared 抓手索引

目前 24 个漏洞专项 Skill 都已经补充"共享抓手索引引用"章节。

这意味着：

- 每个漏洞专项都明确声明以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为基础检索索引
- 每个漏洞专项都要求在共享抓手之上补充项目内私有封装抓手
- 各专项的枚举规则不再彼此漂移，后续维护时也更容易保持一致

### 5. dotnet-audit-pipeline 补强为统一编排入口

dotnet-audit-pipeline 现在已明确：

- 必须读取哪些 shared 规则
- 每个阶段消费什么输入、产出什么结构化结果
- framework_audit 与 route_tracer 如何被后续漏洞专项显式消费
- 最终报告至少要有哪些覆盖矩阵和冲突保留章节

这次补强后，dotnet-audit-pipeline 不再只是一个"汇总说明"，而是整个 .NET Skill 库真正的协调入口。

> 📋 第二轮增强内容（详细记录）已移至 `docs/memory/CHANGELOG_AND_DECISIONS.md`

## 2026年7月 CodeGraph 集成增强（第二十七轮之后）

### 目标

将 CodeGraph 预索引代码知识图工具集成到审计流水线中，在阶段 0 强制建立索引；索引成功时作为 route-mapper 与 route-tracer 的加速器，失败时自动回退静态分析。

### 新增 Skill

- `dotnet-codegraph-indexer`：检测 CodeGraph 环境、建立/刷新索引、产出索引状态文件

### 修改的 Skill

| Skill | 改动内容 |
|-------|----------|
| `dotnet-audit-pipeline` | 阶段 0 新增 CodeGraph 索引建立；输出目录增加 `codegraph/`；编排原则中增加 codegraph-indexer 调度 |
| `dotnet-route-mapper` | 新增 CodeGraph 加速分支：优先通过 `codegraph_explore` 获取 Controller/Action/路由映射 |
| `dotnet-route-tracer` | 新增 CodeGraph 加速分支：优先通过 `codegraph_callers` / `codegraph_impact` 获取跨文件调用链与 DI 解析链 |

### 修改的 shared 规范

- `DOTNET_AUDIT_GRABBER_INDEX.md`：新增「跨文件调用链工具（可选加速）」章节，列出 CodeGraph 各命令用途与约束
- `IO_PATH_CONVENTION.md`：新增 `codegraph/` 目录、新增 `codegraph_index_status_{timestamp}.md` 与 `codegraph_index_validation_{timestamp}.md` 路径映射

### 执行顺序更新

```
dotnet-codegraph-indexer（必选前置步骤；不可用则记录原因并回退静态分析）
  → dotnet-route-mapper → dotnet-auth-audit(STATIC) → dotnet-vuln-scanner
  → dotnet-route-tracer → framework_audit → vuln_audit(各专项)
  → dotnet-exploit-chain-audit → 汇总报告
```

### 关键约束

- CodeGraph 是**必选前置工具**，索引失败必须记录原因并落盘状态文件，后续 Skill 自动回退静态分析
- 无索引时，route-mapper / route-tracer 100% 回退现有静态分析流程
- CodeGraph 返回的符号与调用链仍需与源码片段交叉验证，差异项标记 `⚠️需人工复核`

## 2026年8月 P0/P1 结构化改造

### 新增 Pipeline 阶段（4 个）

| 阶段 | Skill | 类型 | 说明 |
|------|-------|------|------|
| 扫描阶段 | `dotnet-scan-audit` | 审计 | 全量代码扫描，产出 route_mapping 基线 |
| 覆盖补检 | `dotnet-coverage-audit` | 审计 | 增量变更触发补检，维护覆盖率状态 |
| 候选参数 | `dotnet-briefing-agent` | Agent | 生成候选漏洞参数清单，支撑 PoC 构造 |
| 证据质检 | `dotnet-review-agent` | Agent | 证据链闭合性校验、Severity 一致性核对 |

### 现有专项深度改造（2 个）

| 专项 | 改造内容 | 影响 |
|------|----------|------|
| `dotnet-sql-audit` | 新增 Barrier 验证节（白名单/参数化/上下文三层屏障） | SQL 注入审计精确度提升，误报降低 |
| `dotnet-second-order-audit` | 引入 `source_write_entry` / `source_trigger_entry` 深度区分 + 三层验证判定矩阵 | 二阶注入审计从"存储后触发"升级为精确责任分离模型 |

### 共享模板升级（2 个）

| 模板 | 升级内容 | 影响范围 |
|------|----------|---------|
| `DOTNET_VULN_POC_TEMPLATE.md` | 新增排除链（Barrier 通过时标记不可利用） | 所有漏洞 PoC |
| `DOTNET_ROUTE_OUTPUT_TEMPLATES.md` | 新增 `taint_nodes` 结构化字段定义（6 种 taint_type） | 所有路由/追踪/审计产出 |

### Pipeline 融入

`dotnet-audit-pipeline` 已更新子 Skill 对照表与输出目录结构，新增 4 个阶段的标准化接入点。

### 产出目录扩展

新增以下目录：
- `coverage/`：覆盖补检结果
- `briefing/`：候选参数清单
- `quality/`：证据质检结果（已有，现强化为正式阶段产物）

### 变更日志

详细变更记录见：`CHANGELOG-P0P1.md`

### 向后兼容性

- **破坏性变更**：`dotnet-second-order-audit` 结论格式升级（旧版 `已确认/待验证` → 新版含三层判定矩阵）
- **非破坏性变更**：`taint_nodes` 为新增字段；Barrier 验证节为新增章节；Pipeline 新增阶段为可选触发

### 一致性验证

本次改造已通过跨文件一致性检查：
- ✅ 9 个核心文件全部存在
- ✅ taint_nodes 结构一致
- ✅ Pipeline 子 Skill 引用对齐
- ✅ Severity 评级一致
- ✅ YAML 名称-目录对齐

> 验证时间：2026-08-14

---

## 2026年8月 通用执行标准与 Barrier 验证矩阵强化

### 目标

为所有漏洞专项引入统一的执行标准，解决审计过程中"结论漂移、barrier 验证缺失、测试覆盖不足"的问题。通过共享文档 + 专项适配的方式，确保二阶段判定、fail-close 评估、命中 ID 追踪和测试建议成为所有漏洞专项的强制要求。

### 新增共享文档

| 文档 | 路径 | 作用 |
|------|------|------|
| `DOTNET_AUDIT_EXECUTION_STANDARD.md` | `skills/shared/` | 通用执行标准真源：二阶段判定流程、fail-close 三级判定、Barrier 验证通用动作、测试要求、命中 ID 规范 |

### 专项同步改造（全部漏洞/框架专项）

以下漏洞专项已按通用执行标准完成深度改造，新增 Barrier 验证矩阵、二阶段判定、判定规则、测试建议章节，最小输出片段追加 `命中ID` 与 `test_id`：

| 专项类别 | 数量 | 状态 |
|----------|------|------|
| 注入类 | 10 | ✅ 已完成 |
| Web 安全 | 7 | ✅ 已完成 |
| 文件操作 | 5 | ✅ 已完成 |
| 协议与头部 | 3 | ✅ 已完成 |
| 配置与加密 | 3 | ✅ 已完成 |
| 业务逻辑 | 4 | ✅ 已完成 |
| 框架专项 | 9 | ✅ 已完成 |
| **合计** | **41** | **✅ 全部完成** |

> 注：`dotnet-archive-extract-audit` 原为 C5 批次遗漏项，已在本轮补全 Barrier 验证矩阵与二阶段判定。

### 模板升级

| 模板 | 升级内容 | 影响范围 |
|------|----------|---------|
| `DOTNET_VULN_SKILL_TEMPLATE.md` | 新增 Barrier 验证矩阵、二阶段判定、判定规则、测试建议章节模板；最小输出片段追加 `命中ID：M{hash}` 与 `test_id：T{hash}` | 所有后续新增漏洞专项 |
| `DOTNET_FRAMEWORK_SKILL_TEMPLATE.md` | 同上，适配框架专项语境 | 所有后续新增框架专项 |

### 关键约束

1. **Barrier 验证矩阵（强制）**：每个漏洞专项必须包含 `B1/B2/B3` 三级 fail-close Barrier，任一未通过即终止判定
2. **二阶段判定（强制）**：阶段一结构命中 → 阶段二语义确认 → 结论输出（FOUND / PENDING_VERIFICATION / NO_FINDING）
3. **命中 ID（强制）**：每个漏洞结论必须附带 `命中ID：M{hash}`，用于跨产物追溯
4. **test_id（强制）**：每条测试验证必须记录 `test_id：T{hash}`，与命中 ID 关联
5. **结论三档**：`FOUND` / `PENDING_VERIFICATION` / `NO_FINDING`，禁止留空或使用软化措辞

### 向后兼容性

- **非破坏性变更**：Barrier 验证矩阵、二阶段判定、判定规则、测试建议均为新增章节
- **最小输出片段**：追加 `命中ID` 与 `test_id` 字段，旧输出仍可兼容
- **共享标准引用**：各专项通过引用共享文档实现，不改变原有核心逻辑

本次改造已通过跨文件一致性检查：
- ✅ 全部 41 个漏洞/框架专项 SKILL.md 已包含 Barrier 验证矩阵
- ✅ 全部 41 个专项已追加 `命中ID` 与 `test_id` 到最小输出片段
- ✅ `DOTNET_VULN_SKILL_TEMPLATE.md` 与 `DOTNET_FRAMEWORK_SKILL_TEMPLATE.md` 已同步模板
- ✅ `CLAUDE.md` 与 `README.md` 已更新 Skill 必要章节与共享规范说明

> 验证时间：2026-08-19

## 第四十一轮 A 类快速修复（2026-09-18）

依据 `docs/2026-09-18-真实审计验证回录与修复规划.md` 与同事真实 run 回录，对 6 项既有共享契约缺陷做快速修复（模板/脚本小改，非新机制）：

1. **P0-1 路由计数自检**：route 输出模板新增 routes 计数对账节与检查点计数自检门禁，route-mapper 强制落账
2. **P0-2 双字段计数口径统一**：IO 约定与双栈 route 模板强制 `unique` / `method_path_count` 双字段口径，contract-mapper 三桶分母锁定 `method_path_count`
3. **P0-3 WARN 对账脚本化**：`scripts/validate_audit.py` 新增路由计数 / exploit / final_anchor 对账与 consistency 归并探测共 4 项检查
4. **P1-6 编排去轮询**：fullstack-audit-pipeline 改为 PHASE_STATUS 里程碑回写替代磁盘轮询；`shared/PHASE_STATUS.md` 成为 manifest 里程碑行格式唯一真源，dotnet / node pipeline manifest 节对称引用
5. **P1-8 node consistency 产物对称**：node consistency_check 升格为强制产物，并引用双栈同构归并标记格式
6. **P2-14 最终报告分级详略规则**：`shared/FULLSTACK_FINAL_REPORT_FIXED_TEMPLATE.md` 固化分级详略强制规则

### 关键约束

- 计数铁律零漂移：dotnet 53 / node 49（合计 106）/ 漏洞专项 35 / node 31 全部不变，本轮无 skill 增删
- 验收基线不变：`scripts/validate_audit.py scripts/_demo_audit/` 输出保持 `PASS=1 FAIL=4 WARN=17`

> 验证时间：2026-09-18

## 第四十二轮 B 类机制扩展（2026-09-18）

依据 `docs/superpowers/specs/2026-09-18-b-class-mechanism-extensions-design.md` 与「先登记、后实施」约定，B 类机制扩展批 7 条全部接入既有 Skill / pipeline，不新增目录（16 实施 commit + 3 复核补齐 + 收尾，台账 7 条翻转「已实现，待验证」）：

1. **P1-4 阶段 0.7 递归探测 + 否定结论复核**：design_intent 探测改递归 glob（`**/docs/superpowers/`、`**/.superpowers/sdd/`、`**/docs/design/`），子流水线对「未发现」否定结论执行廉价独立复核；产物新增 `search_scope` 自证块（§9 增补规则⑤⑥，肯定结论不需复核）
2. **P2-12 意图源白名单扩展**：ADR/RFC 类决策目录纳入可配置意图源白名单，同六节摘要提炼，红线不变
3. **P1-5 阶段 6 顺序约束**：contract-mapper 先行落地产物，consistency-audit / taint-linker 按依赖序启动，消除输入竞态
4. **P1-7 待补证风险池统一 schema**：七字段 schema + `quality/pending_pool_{timestamp}.md` 单一真源，收尾自动聚合，validate 新增两项可选对账
5. **P2-13 内嵌异栈项目检测**：stack-detect 新增「## 内嵌异栈项目」节与归属决策表三态（样例 / 生产引用 / 仅文档），GC6 例外说明，不允许留空
6. **P2-11 供应链离线增强**：扫描产物新增 `knowledge_cutoff_date` 与 `offline_report_source` 字段，支持用户注入离线 audit 报告
7. **专项派发核对**：漏洞专项 index 模板与编排层触发清单三态核对（触发 / 否定证据 / 不适用），杜绝静默漏派发

### 关键约束

- 计数铁律零漂移：dotnet 53 / node 49（合计 106）/ 漏洞专项 35 / node 31 全部不变，本轮无 skill 增删
- 验收基线不变：`scripts/validate_audit.py scripts/_demo_audit/` 输出保持 `PASS=1 FAIL=4 WARN=17`；P1-4 已经 dogfood + 故障注入自检，其余 6 项待下次真实 run 回录

> 验证时间：2026-09-18

## 第四十三轮 C 类 architectural 首项（2026-09-19 node-feature-api-mapper 功能↔API 映射层）

依据 `docs/superpowers/specs/2026-09-19-node-feature-api-mapper-design.md` 与 2026-09-19 brainstorming 立项（三决策均取 A 方案），C 类 3 项 architectural 首项 P2-9 功能↔API 映射层完成 spec→plan→SDD 四批实施（skill 本体 → 消费接入 → pipeline 接入 → 收尾）：

1. **新建 `node-feature-api-mapper`**：功能面→端点→后端 route_id 三层映射（SPA 路由表扩展 / 组件树 import 反向索引 ≤6 层 / client 方法→端点复用 frontend_outbound rg 规则）；穿透白名单三模式穿透一层；断链三分类强制兜底（禁止静默丢弃，PARTIAL 循环补图）；产物 `feature_api_map_{timestamp}.md`（头部四强制字段 + 三节模板）；纯 BFF 无 SPA 项目 fail-open 落 `NOT_APPLICABLE` 探测证据
2. **消费接入**：node-logic-audit「功能面组织判定」、node-auth-audit「功能视图优先（导出/删除/批量/租户/凭据类端点直接 P0）」、dotnet-route-tracer traces_index 增 `feature` 列（fullstack 反查 feature_api_map；单栈控制器域启发式，标注非证据）
3. **Pipeline 接入**：fullstack 阶段 6 插 P1.5（contract-mapper 之后，衔接第四十二轮 P1-5 顺序约束）；node pipeline 可选阶段 1.8；PHASE_STATUS 表增交付态行
4. **产物红线**：全部产物属视图层参考，禁止作 EVID 证据源（design_intent §9 同红线）；与代码不一致以代码为准，登记「功能视图-实现漂移」治理发现

### 关键约束

- 计数演进：node 49→50、总数 106→107（批 1 创建目录即全库同步）；skill 目录改名 `node-feature-api-mapper` 补齐 node 家族命名公约，`ls skills/ | grep -c '^node-'` = 50 字面成立；漏洞专项计数 dotnet 35 / node 31 不变；历史轮次条目旧计数属历史记录不改
- 验收基线不变：`scripts/validate_audit.py scripts/_demo_audit/` 输出保持 `PASS=1 FAIL=4 WARN=17`；EVID 零新增
- 台账 `node-feature-api-mapper` 翻转「已实现，待验证」（dogfood NOT_APPLICABLE 探测 + scratch 故障注入双路径经独立复核复现；待下次真实 run 回录）；待验证计数 14 → 15

> 验证时间：2026-09-19

## 第四十四轮 C 类 architectural 第二项（2026-09-19 DYNAMIC_VERIFY(STATIC_UNIT) 动态验证阶段，P2-10）

依据 `docs/superpowers/specs/2026-09-19-dynamic-verify-unit-design.md`，C 类 3 项 architectural 第二项 P2-10 动态验证阶段完成 spec→plan→SDD 三批实施（schema+shared 模板 → 双 pipeline 阶段 7+语义衔接 → 收尾）：

1. **pending_pool schema 扩展**：「闭合方式」三枚举（`static-evidence` / `dynamic-unit` / `needs-env`）+ 条目状态枚举（`OPEN` / `DYNAMIC_VERIFIED`）+ 状态分桶计数（`open_count` / `dynamic_verified_count`，`pool_total` 口径不变）+ 历史产物启发式推断（`skills/shared/IO_PATH_CONVENTION.md`）
2. **新建 `skills/shared/DYNAMIC_VERIFY_UNIT_TEMPLATE.md`**：红线四零自检（零凭证/零网络/零服务/零 scratch 目录外写入）+ dotnet xunit / node vitest 双测试工程骨架（复制不引用）+ 运行与回写协议
3. **双 pipeline 可选阶段 7**：dotnet-audit-pipeline / node-audit-pipeline 各插「阶段 7：DYNAMIC_VERIFY(STATIC_UNIT)」（可选，fail-open）；「已确认（动态验证）」两级语义原文零改动，仅追加交叉引用一句（唯一合规触发路径）；IO_PATH_CONVENTION 登记 dynamic_verify 产物路径

### 关键约束

- 机制扩展三件套不建 skill 目录：计数 53/50/107 不变；EVID 零新增
- 保守语义：FAILED 保持 OPEN、needs-env 跳过、任何结果不改 `audit_surface_status` 判定；批 2 复核保守语义 diff 零删改亲验
- 集成级动态验证（服务启动/测试租户/凭证托管）明确另立项，本阶段仅 STATIC_UNIT 范围
- 验收基线不变：`scripts/validate_audit.py scripts/_demo_audit/` 输出保持 `PASS=1 FAIL=4 WARN=17`
- 台账 P2-10 翻转「已实现，待验证」（故障注入三案例走查 A:VERIFIED 状态翻转 / B:FAILED 保持 OPEN / C:needs-env 跳过经独立复核复验；待真实 run 回录）；待验证计数 14 → 15（grep 实数）
- 批 2 复核遗留 2 补句各独立 commit：阶段 7 与最终报告风险池计数引用顺序说明（双 pipeline）；node pipeline 风险池引用路径前缀对齐 `node/quality/` 口径

> 验证时间：2026-09-19

## 2026-09-20 真实 run 回录（台账 10 项翻转已验证，待验证 15 → 5）+ 方案A

依据 run `api-main_2026_09_20_10_38` 产物（`temp/apccr_fullstack_audit_feedback_2026_09_20/api-main_fullstack_audit/`，只读参考）对台账 15 项待验证全量核验，结论 10 通过 / 5 不通过：

1. **回录**：10 项翻转「已验证」附证据——`dotnet-ai-prompt-audit`（派发核对节显式不适用附理由）/ `node-feature-api-mapper`（四字段齐备 11 功能/97 端点/COMPLETE）/ P2-10 DYNAMIC_VERIFY（NOT_RUN + 红线四零逐项核验 + dynamic-unit 7 条保持 OPEN）/ P1-4 阶段 0.7（search_scope 六模式自证 + 双栈 AGREE(65)）/ P2-12 白名单（adrs 3 命中 / rfcs 0 已核实）/ P1-5 阶段 6 顺序（消费 contract_map 桶无矛盾）/ P1-7 pending_pool（74/72 分桶 + §7 强制引用）/ P2-13 内嵌异栈（三态登记 + M-CRYPTO-002）/ 专项派发核对（双栈 51/49 行全三态无裸「未触发」）/ dotnet-config-audit 配置暴露扩展（三维度齐备）；5 项保持待验证并登记失败根因（账号枚举 / 日志篡改淹没 / 签名重放 / 整数溢出 dotnet 侧零提及无否定证据 + P2-11 半通过 node 字段齐备 dotnet 缺字面字段），待验证计数 15 → 5
2. **方案A**：问答场景否定结论双通道纪律写入 4 个 agents 定义 + 双 pipeline 0.7 补存在性排查强制条款（同日 5 commit：`f32cd3e` / `16ec33c` / `c125b46` / `63910ae` / `a89956a`）；非新机制，台账维护日志按批次记录

### 关键约束

- 5 项失败系统根因一句话：维度级枚举未入专项强制清单，专项内维度静默缺失不受派发核对覆盖（派发核对只管专项级）——已并入缺陷批输入
- 台账 10 项状态行 + 验证证据行翻转、5 项验证证据行更新、维护日志追加回录批次记录；机制正文零改动
- 下一步：缺陷批立项（同事 12 项 + 本次 5 项失败合并规划，含「维度级派发核对」新机制设计）

> 验证时间：2026-09-20

## 第四十五轮（2026-09-20 缺陷修复批，17 项缺陷归 3 批 SDD 交付）

依据 `docs/superpowers/specs/2026-09-20-defect-fix-batch-design.md`，真实 run 回录 5 项失败 + 同事 12 项反馈合并 17 项缺陷，spec→plan→SDD 三批实施（批间两阶段复核 ×3 全通过 + 复核遗留 2 补句各独立 commit）：

1. **批 1 计数与口径闭合**：pending_pool 一 id 一行禁别名合并 + 三公式固化（`pool_total`=唯一 pool_id 数 / 统计表计数=详情枚举数 / closed=非误报非 pending 之和）+ final_anchor 机器校验三行 + `run_timestamp` 全栈统一下发双栈 + SEVERITY 定级枚举闭合 C/H/M/L（禁区间值，升级通道注记「建议升 M」）
2. **批 2 流程缺口修补**：stack_detect 子流水线强制交付 + 阶段 0 末 Test-Path 检查清单（缺即 BLOCKED）+ 共享索引单写者原则（分片命名归编排层合并）+ 「pool 行先于引用」强制条款 + 阶段 0 preflight 环境核查（`preflight_{timestamp}.md` 双栈）+ 等待超时量化公式（预计分钟=2+总文件数千分位×8）+ 阶段 6 P2 隐藏面 trace 编排层直执 + node-route-mapper 方法级配对强制（禁双方法保守上界）
3. **批 3 维度级派发核对（本批核心）**：IO 状态模型「维度核对」条款（台账登记机制扩展维度逐条三态，禁裸「未覆盖」，真源=台账覆盖机制字段，双 pipeline 阶段 4 引用）+ 4 专项强制枚举清单增维度条（auth 错误响应一致性 / logging 篡改+淹没 / crypto+webapi 签名重放 / logic 整数溢出）+ 字段级合规矩阵（`knowledge_cutoff_date` / `offline_report_source` 字面字段必含 + 动态验证报告红线表头逐字对齐四零条款）

### 关键约束

- 维度级派发核对 = 防「专项内维度静默缺失」从专项级下沉到维度级；不改既有专项级派发核对语义
- 全批零代码零 validate 新增：计数 53/50/107 不变、基线 `PASS=1 FAIL=4 WARN=17` 不变、EVID 零新增；红线回归（专项派发核对语义/SEVERITY 既有等级定义/pending_pool 八字段/§9 四规则/回录 10 项证据行）零删改
- 台账第四十五轮批 1/批 2/批 3 三条翻转「已实现，待验证（2026-09-20 第四十五轮交付）」；待验证计数 5 → 8
- 交付：24 实施 commit + 2 复核补句 commit + 收尾 1 commit，合计 27 commit
- 遗留输入：`node-route-mapper` frontend_outbound 出站条目混入 unmapped 列结构，待规范化

> 验证时间：2026-09-20

## 第四十六轮（2026-09-21 复审修补批，打包前三路独立复审驱动）

依据 `docs/superpowers/specs/2026-09-21-review-fix-batch-design.md`，打包前三路独立复审（设计合理性 / 落地真实性 / 一致性回归）暴露 20 项缺口（2 高 8 中 10 低），spec→SDD 两批实施（批间复核：快照-台账一致性自查 A8/B11 全对账 + no-op 核对通过）：

1. **批 1 执行闭环断点修复**：维度清单包内快照（IO_PATH_CONVENTION 附录 A8+B9，执行真源 / 登记真源双轨）+ 子栈 run_timestamp 双模接住（fullstack 编排模式接收下发不自产 / 单栈模式自产，堵双时间戳复活口）+ BLOCKED 恢复闭环单栈断环修复（阶段 0 末清单补双模恢复动作）+ manifest 映射表格式登记 + 里程碑行时间戳钉死 run_timestamp + 公式③链状态口径登记（closed/open/误报/pending 四态映射表）+ final_anchor 三行机器校验字段 + preflight 产物模板
2. **批 2 维度清单包内化 + 记录层打磨**：快照补登 B10/B11 + 完整性口径句 / unmapped 落点规范化（方法不确定入 frontend_outbound 自备清单节、禁写 unmapped_routes）/ 待补证池 CLOSED 枚举（静态/阶段内闭合）+ closed_count 分桶归并 / frontend_outbound IO 路径真源登记（route_mapping 产物表增行）/ 方案A纪律排除句（rg 零命中非资产存在性结论，4 agents 各加一行）/ 等待超时取整规则（不取整连续计算、四舍五入到分钟）+ 总文件数 GC6 口径 / preflight 级联规则登记 / SEVERITY 定级统计分组按枚举值 / 链状态态名对照（pending↔open 同义同集）/ node pipeline 单栈维度核对引用句 / 维护日志 + CHANGELOG 记录层勘误（缺陷项数 16 口径）

### 关键约束

- 维度清单双轨制：包内快照=执行真源，台账=登记真源（新维度先登记→快照同步，打包时对账；漂移以台账为最终真源并须同步快照）
- 全批零代码零 validate 新增：计数 53/50/107 不变、基线 `PASS=1 FAIL=4 WARN=17` 不变、EVID 零新增
- 台账第四十六轮条目翻转「已实现，待验证（2026-09-21 第四十六轮交付）」；待验证计数 8 → 9
- 缺陷项数口径统一为 16（同事反馈 11 条 + 回录失败 5 项；此前「17 项」系同事 #2 拆为两项计数所致，口径统一说明句见台账维护日志与 CHANGELOG 第四十五轮勘误）
- 遗留输入清零：第四十五轮「node-route-mapper frontend_outbound 出站条目混 unmapped 列结构」遗留批 2 规范化落点清零
- 交付：18 实施 commit + 1 口径统一 commit + 收尾 1 commit，合计 20 commit

> 验证时间：2026-09-21

## 第四十七轮（2026-09-21 门禁收尾批）

台账机器校验落地（validate 新增 Ledger 检查：状态枚举 / 必填字段 / 待验证计数对账，通过静默保基线 PASS=1）+ W 检查增强（台账 ACTIVE 专项数 vs 核对节行数，单向漏核触发）+ final_anchor 机器校验脚本化（X 检查：pool_check / stat_check / chain_check FAIL 检出 + 池计数=唯一 id 数重算）+ `traces_index_{timestamp}.md` 输出模板节（批次列表含 feature 列，46 轮规则落模板）；基线 `PASS=1 FAIL=4 WARN=17` 不变、计数 53/50/107 不变、EVID 零新增、待验证计数 9 → 10。

> 验证时间：2026-09-21
