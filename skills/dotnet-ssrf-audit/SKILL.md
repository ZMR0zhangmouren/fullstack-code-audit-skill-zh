---
name: dotnet-ssrf-audit
description: .NET SSRF 审计工具。识别用户可控 URL 进入 HttpClient、WebRequest、Webhook 或内部调用客户端的风险路径。
---

# .NET SSRF 审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与 URL 来源、HTTP 客户端、Webhook、回调、代理和协议限制相关的共享抓手
- 若项目存在 ApiClient、WebhookSender、HttpGateway、CallbackService 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（用于对齐请求发起入口、URL 来源与 `route_id`）
- 可选：`framework_audit/*_{timestamp}.md`（用于补充代理、宿主、网络边界与运行时控制面）
- trace-gate 场景下优先消费：`route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline` 执行，当前专项引用的 `route_id` 应与 `cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- HttpClient、HttpRequestMessage、SocketsHttpHandler、WebRequest、RestSharp 或第三方 SDK 的请求发起点
- URL 从 Route、Query、Body、配置、数据库、消息队列、GraphQL 参数或 Hub 消息中进入请求构造的路径
- Uri、UriBuilder、Path/Query 拼接、协议相对地址、双重编码、用户名密码段、IPv6、十进制/八进制 IP 表示处理
- 自动跟随重定向、代理配置、DNS 解析、Host 头重写、X-Forwarded-* 信任边界与二次跳转
- webhook 回调、开放抓取、文件/图片下载、OpenID/OAuth discovery、S3/Blob 同步、GraphQL schema introspection 拉取等业务场景
- 对 localhost、169.254.169.254、云元数据、内网 CIDR、Unix socket、gopher/file 等危险协议或地址的限制是否有效
- 结果回显、错误信息、下载内容转存、后续解析或服务端探测能力是否扩大利用影响

## 枚举规则（强制细化）

- 枚举 HttpClient、HttpRequestMessage、WebRequest、RestSharp、Refit、GraphQL 客户端、Webhook 客户端、自定义下载器
- 优先搜索 URL、Uri、BaseAddress、RequestUri、Location、callback、webhook、avatar、download、proxy 等关键字段
- 枚举所有外部请求发起前的 URL 拼接、规范化、redirect 跟随、DNS 解析与代理配置逻辑
- 对每个请求点记录：来源参数、协议限制、host allowlist、内网/metadata 防护、最终返回内容去向

## Barrier 验证矩阵（强制）

本专项必须对以下 barrier 类型执行验证，按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 标准评估：

| Barrier 类型 | 验证动作 | 判定标准 |
|-------------|---------|---------|
| **URL 解析后 host/ip 校验** | 读取 host allowlist/denylist 实现源码，确认是基于解析后的 host/ip/端口做校验（非字符串黑名单） | fail-close（解析后拒绝未知 host） → ✅ 安全；字符串黑名单（如 `Contains("localhost")`） → ⚠️ 可绕过；无校验 → 🔴 高危 |
| **协议限制** | 确认是否限制请求协议为 `http`/`https`，禁止 `file://`、`gopher://`、`dict://`、`ftp://` 等 | 严格限制且不可绕过 → ✅ 安全；仅前端限制或可通过编码绕过 → ⚠️ 可绕过；无限制 → 🔴 高危 |
| **重定向跟随策略** | 确认 `AllowAutoRedirect` 或自定义重定向处理，跟随后是否重新执行 host/ip 校验 | 跟随后二次校验 → ✅ 安全；跟随但不二次校验 → 🔴 高危；不跟随重定向 → 🟠 需评估业务影响 |
| **内网/CIDR/元数据拦截** | 确认是否拦截 IMDS（`169.254.169.254`）、内网 CIDR（`10.0.0.0/8`、`172.16.0.0/12`、`192.168.0.0/16`、`127.0.0.0/8`） | 完整拦截且不可绕过 → ✅ 安全；仅拦截部分段或绕过方式已知 → ⚠️ 可绕过；无拦截 → 🔴 高危 |
| **DNS 重绑定防护** | 确认是否存在 DNS rebinding 防护（如解析后二次校验、TTL 检查、IP 缓存锁定） | 有二次校验/IP 锁定 → ✅ 安全；仅依赖 DNS 解析结果不做二次校验 → ⚠️ 待确认 |
| **代理与转发信任边界** | 确认是否盲目信任 `X-Forwarded-Host`、`X-Forwarded-Proto` 等头，是否存在 Host 头注入绕过 allowlist 的可能 | 严格校验或不信任外部转发头 → ✅ 安全；信任外部传入的转发头 → ⚠️ 可绕过 |

🔴 **STOP：任一 barrier 验证为 `silent-fallback` 或 `fail-open` 时，禁止将结论标记为「已确认安全」或「误报」。**

## 二阶段判定（强制）

遵循 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

1. **阶段一（临时结论）**：对每条命中先标记 `确认漏洞候选` / `待确认` / `误报`
2. **阶段二（强制追证）**：
   - 若阶段一为 `确认漏洞候选` → 必须完成 Barrier 验证矩阵全部相关项，通过后才能标记 `已确认`
   - 若阶段一为 `待确认` → 必须向下追至少一跳调用链或下游解析器，直到可判定为止
   - 若阶段二仍无法闭合 → 保持 `待确认`，并明确记录缺失哪一跳证据

## 判定规则（强制细化）

### 确认漏洞

至少满足以下任一条件：

1. 用户可控 URL 直接进入 `HttpClient`、`WebRequest`、`RestSharp` 等请求构造，且无 host/ip/端口校验
2. Host allowlist 为 `fail-open` 或 `silent-fallback`，或基于字符串黑名单而非解析后校验
3. 重定向自动跟随且跟随后未重新执行 host/ip 校验
4. 存在 DNS rebinding 可行路径（解析前 host 在 allowlist，解析后指向内网/元数据地址）
5. 嵌套/递归结构（如多层 ApiClient 封装）中顶层存在校验，但子层未执行同级校验

### 待确认

1. 上下文显示可疑模式（如 `HttpClient.SendAsync` 调用），但外部输入来源不清晰（需补 trace 或调用链）
2. Barrier 函数（如 host allowlist）存在，但当前分支是否调用、返回值是否被使用无法确认
3. 异步 / 队列 / 事件链路（如消息队列消费 webhook 回调）中的参数传递未闭合
4. 重定向策略存在但实现不可见（如自定义 `RedirectHandler` 行为不确定）

### 误报

1. 最终请求目标来自固定常量 / 枚举映射，未知 host 会拒绝执行（fail-close allowlist）
2. 递归所有层级均复用同一解析后 host allowlist 校验器，且 allowlist 为 fail-close
3. 请求目标为固定 base URL，用户仅控制 path/query 且 path/query 经过严格校验
4. 无重定向跟随，且 host 校验在解析后执行并锁定 IP（防 DNS rebinding）

## 测试建议（强制）

遵循 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的测试要求，对每个确认漏洞或待验证项给出：

- **正向测试**：构造指向 `169.254.169.254`（IMDS）、`localhost`、`127.0.0.1`、内网 IP（如 `10.0.0.1`）的请求，验证 SSRF 确实存在
- **负向测试**：构造被 allowlist 拦截的 host（如 `evil.com`）、非法协议（如 `file:///etc/passwd`），验证保护机制有效
- **回归测试**：修复后复测，确认 barrier 仍然生效，且未引入新的绕过路径（如重定向绕过、DNS rebinding）

测试用例应标注 `test_id`，并在审计报告中与对应命中 ID 关联。

## 证据引用

- EVID_SSRF_URL_NORMALIZATION
- EVID_SSRF_FINAL_URL_HOST_PORT
- EVID_SSRF_DNSIP_AND_INNER_BLOCK

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（请求面识别）**：必须确认所有外联 HTTP/Socket/DNS 入口与可控参数。
- 🔴 **CHECKPOINT B（目的端约束）**：必须确认 allowlist/denylist、协议与端口限制、重定向策略。
- 🔴 **CHECKPOINT C（云元数据保护）**：必须确认 IMDS/内网段拦截与旁路策略。
- 🛑 **STOP**：若关键目的端限制缺失或可被绕过，禁止输出“低风险”结论。

## 失败场景与兜底（if-then）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| URL 来源到请求发起链不完整 | 回溯到 RequestUri/BaseAddress 构造点 | 降级 `⚠️待验证` |
| 解析后 host/ip/端口约束不明确 | 补齐 normalize 与解析后校验证据 | 不输出低风险结论 |
| 重定向与内网拦截策略证据不足 | 验证二跳重检与 IMDS/CIDR 防护 | 保守评估并保留待补证项 |

🔴 **STOP：任一兜底触发时，禁止输出“低风险”。**

## 资源引用与可达性校验（强制）

- 必引共享索引：`skills/shared/DOTNET_AUDIT_GRABBER_INDEX.md`（抓手来源）与 `skills/shared/EVIDENCE_POINT_IDS.md`（证据口径）。
- 输出口径校验：落盘路径与命名必须对齐 `skills/shared/IO_PATH_CONVENTION.md`，不得自定义偏离目录。
- 证据一致性校验：若引用分级结论，需与 `skills/shared/SEVERITY_RATING.md` 保持一致。
- 可达性检查：提交前至少确认一次关键引用文件可访问（例如 `DOTNET_AUDIT_GRABBER_INDEX.md`、`IO_PATH_CONVENTION.md`）。

## 实测用例与通过标准（强制）

- 每个 skill 至少维护 2 个典型测试用例（happy path + 一条复杂场景），并在结果中标注用例 ID。
- 每轮评估至少 1 条用例执行 `full_test`；若受限只能 `dry_run`，必须记录 `dry_run_reason` 与补测计划。
- 通过标准至少同时满足：`意图达成`、`关键证据命中`、`输出格式合规`；任一不满足不得给出“通过”。

## 整体架构与冗余控制（强制）

- 章节组织必须保持三层骨架：`输入约束` → `执行步骤` → `输出与验收`，不得缺层或跨层混写。
- 单段建议不超过 6 行；同义规则禁止重复出现两次以上，重复内容需合并到唯一真源章节。
- 禁止 AI 腔与空话衔接词堆叠（如“首先/其次/最后/综上/说白了/换句话说”）；发现即改为可执行语句。

## 质量门禁与评估一致性（强制）

- 产出前必须执行最小门禁自检：`输入完整性`、`关键证据命中`、`输出路径合法` 三项全部为 PASS。
- 若存在 `关键证据缺失`、`链路未闭合`、`consistency_check_status=BLOCKED` 任一条件，结论必须降级为 `BLOCKED`，禁止输出“确认可利用/可交付”。
- 报告中必须显式记录：`gate_status`、`blocked_reasons`、`recheck_action`，并与 `quality/*` 产物可回溯对齐。

## 不要做的事（反例黑名单）

- 反模式：仅做字符串黑名单拦截。正确做法：基于解析后 host/ip/端口做校验。
- 反模式：忽略重定向二跳。正确做法：限制并复检每次跳转目标。
- 反模式：只拦 127.0.0.1 不拦云元数据段。正确做法：覆盖 IMDS 与内网 CIDR。
- 反模式：验证缺失却输出低风险。正确做法：保守降级并补证据需求。

## 可执行参数与输出模板（强制）

- 审计结论等级：`已确认` / `⚠️待验证` / `不适用`（三选一，禁止留空）。
- 证据最小集：至少包含 `入口点`、`可控参数`、`关键调用`、`安全边界`、`缺失证据` 五项。
- 输出文件命名：统一使用 `{topic}_{timestamp}.md`，并与 `IO_PATH_CONVENTION.md` 对齐。
- 禁止使用软化措辞：如“可能有风险/建议关注/视情况而定/大概率”等；证据不足时必须明确写 `⚠️待验证` 与下一步补证动作。

最小输出片段（可直接复用）：

```md
- 命中ID：M{hash}（文件路径片段+行号+序号，用于跨阶段追踪和回归对齐）
- 审计结论等级：已确认
- 证据最小集：入口点=...；可控参数=...；关键调用=...；安全边界=...；缺失证据=无
- test_id：T{hash}（关联测试用例）
- 下一步动作：若存在缺口，补 trace_id=... 的参数传播证据
```
- 审计结论等级：已确认
- 证据最小集：入口点=...；可控参数=...；关键调用=...；安全边界=...；缺失证据=无
- 下一步动作：若存在缺口，补 trace_id=... 的参数传播证据
```

## 输出

- vuln_audit/ssrf_{timestamp}.md
- 可选：vuln_poc/ssrf_{timestamp}.md（已确认 / 待验证 / 环境依赖 PoC；如不适合直接构造请求，至少给出验证步骤）
