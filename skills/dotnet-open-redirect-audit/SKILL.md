---
name: dotnet-open-redirect-audit
description: .NET 开放重定向审计工具。识别 Redirect、LocalRedirect、ReturnUrl、Challenge 回跳和登录后跳转中的目标地址控制风险。
---

# .NET 开放重定向审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与 ReturnUrl、Redirect、导航目标、外部地址白名单和代理前缀处理相关的共享抓手
- 若项目存在 RedirectHelper、LoginFlowService、NavigationGuard、CallbackResolver 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（用于对齐跳转入口、ReturnUrl 参数与 `route_id`）
- 可选：`auth_audit/auth_mapping_{timestamp}.md`（用于补充登录/登出/挑战入口的鉴权边界）
- trace-gate 场景下优先消费：`route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline` 执行，当前专项引用的 `route_id` 应与 `cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- Redirect(url) 中 url 来源为请求参数且未做 IsLocalUrl 校验
- OAuth/OIDC 回调中的 redirect_uri / post_logout_redirect_uri 校验
- 登录/登出流程中的 ReturnUrl / next / continue 参数
- LocalRedirect 是否真的限制了本地跳转（PathBase 影响）
- Challenge / SignOut 后的跳转地址可控性
- 支付回跳、邀请链接、深链跳转中的目标地址校验
- 协议限制：是否允许 javascript: / data: / 相对协议 URL

## 证据引用

- EVID_REDIR_OUTPUT_POINT
- EVID_REDIR_DEST_SOURCE_MAPPING
- EVID_REDIR_DEST_VALIDATION_NORMALIZATION

## 枚举规则（强制细化）

- 枚举所有 Redirect、LocalRedirect、RedirectToAction、Challenge、SignOut、returnUrl / next / continue / callback 参数处理逻辑
- 优先搜索 IsLocalUrl、redirect_uri、post_logout_redirect_uri、ReturnUrl、redirectTo、callbackUrl、PathBase 相关代码
- 枚举登录、登出、认证回调、支付回跳、邀请链接、深链跳转、错误回跳等业务场景
- 对每个跳转点记录：目标来源、校验逻辑、外部身份提供方约束、代理头影响、是否携带敏感票据

证据建议：复用 XSS/CFG 的路径归一化思路，并在报告中说明目标校验分支。

## Barrier 验证矩阵（强制）

按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 三级标准评估：

| 等级 | 检查项 | 通过标准 | 失败降级 |
|------|--------|----------|----------|
| 一级 | 跳转点存在且目标来源可控 | Redirect/Challenge/SignOut/ReturnUrl 等跳转点存在且目标参数用户可控 | BLOCKED → 目标来源不可控，专项结束 |
| 二级 | 校验逻辑可绕过 | IsLocalUrl/allowlist/协议限制存在绕过可能（双斜杠/编码/反斜杠/javascript: 等） | BLOCKED → 结论降级为 `⚠️待验证/环境依赖` |
| 三级 | 跳转后果可达敏感操作 | 跳转后可导致凭据泄露、越权访问或敏感操作执行 | PARTIAL → 仅输出绕过假设与验证步骤 |

## 二阶段判定流程（强制）

- **阶段 1（初筛命中）**：命中跳转输出点 + 目标来源为用户输入，输出 `命中ID：M{hash}`。
- **阶段 2（精筛确认）**：
  1. 逆向追踪目标地址来源与参数映射链路；
  2. 验证 IsLocalUrl/allowlist/协议限制/归一化逻辑的绕过条件（双斜杠、编码、反斜杠、PathBase 影响）；
  3. 评估跳转后是否可达敏感端点或泄露凭据；
  4. 若三级 Barrier 全部通过 → `确认漏洞`；任一失败 → 按矩阵降级。

## 判定规则与优先级（强制）

1. **确认漏洞**：跳转点存在 + 目标来源可控 + 校验可绕过 + 可达敏感操作。输出 `确认漏洞`。
2. **待确认**：跳转点与目标映射存在，但校验绕过条件或代理/PathBase 影响证据不足。输出 `待确认`。
3. **误报/无风险**：目标来源不可控（硬编码/内部生成），或校验逻辑严格且归一化完整。输出 `误报` 并给出判定依据。

## 测试建议与最小触发条件（强制）

- **最小触发条件**：
  - 存在 Redirect/LocalRedirect/Challenge/SignOut 等跳转点
  - 跳转目标来源包含用户可控输入（ReturnUrl/next/continue/callback 参数）
  - 目标校验逻辑存在绕过可能（缺少 IsLocalUrl、白名单不完整、未限制协议）
- **测试用例建议**：
  - Happy Path：正常本地路径跳转成功，外部 URL 被拦截
  - 边界/歧义：`//evil.com`、`\\evil.com`、`javascript:alert(1)`、URL 编码绕过、PathBase 前缀绕过
- 每条命中输出追加 `命中ID：M{hash}` 和 `test_id：T{hash}`，用于回溯。

## 工作流（输入→执行→输出）

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（跳转点确认）**：必须确认 Redirect/Challenge/SignOut 等真实跳转输出点。
- 🔴 **CHECKPOINT B（目标映射确认）**：必须给出目标地址来源与参数映射。
- 🔴 **CHECKPOINT C（校验链确认）**：必须确认 IsLocalUrl/allowlist/协议限制是否真实执行。
- 🛑 **STOP**：若目标校验分支不可证实，结论降级为 `⚠️待验证/环境依赖`。

## 失败场景与兜底（if-then）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| 跳转目标来源链不完整 | 补齐参数到 Redirect/Challenge 输出映射 | 降级 `⚠️待验证/环境依赖` |
| 归一化/协议限制证据不足 | 验证双斜杠、编码、反斜杠与 scheme 分支 | 不输出可利用强结论，仅给验证路径 |
| 代理/PathBase 影响不明确 | 对齐部署链路下的最终跳转目标 | 保守评估并保留待补证项 |

🔴 **STOP：任一兜底触发时，禁止输出“已确认可利用”。**

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

- 反模式：见到 Redirect(url) 就直接判漏洞。正确做法：先确认目标来源是否可控。
- 反模式：只检查 IsLocalUrl 不做归一化验证。正确做法：覆盖双斜杠、编码、反斜杠等绕过。
- 反模式：忽略代理与 PathBase 影响。正确做法：按部署边界核验最终跳转目标。
- 反模式：证据链不完整写强结论。正确做法：降级 `⚠️待验证/环境依赖`。

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

- vuln_audit/redir_{timestamp}.md
- 可选：vuln_poc/redir_{timestamp}.md（已确认 / 待验证 / 环境依赖 PoC；如不适合直接构造请求，至少给出验证步骤）
