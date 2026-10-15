---
name: dotnet-session-cookie-audit
description: .NET 会话、Cookie 与 JWT 审计工具。识别 Cookie flags、认证票据轮换、JWT 校验参数和登出清理缺陷。
---

# .NET Session / Cookie / JWT 审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与 Session、Cookie、JWT、票据属性、续期、注销和跨站行为相关的共享抓手
- 若项目存在 TokenService、CookieHelper、SessionManager、AuthCookieFactory 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（用于对齐登录、登出、票据更新入口与 `route_id`）
- 可选：`auth_audit/auth_mapping_{timestamp}.md`（用于补充认证态、匿名入口与权限边界）
- trace-gate 场景下优先消费：`route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline` 执行，当前专项引用的 `route_id` 应与 `cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

重点检查：

- Cookie flags：HttpOnly、Secure、SameSite、Domain、Path、IsEssential、Persistent、SlidingExpiration 以及跨子域共享策略
- 登录、权限提升、2FA 完成、租户切换、模拟登录后是否轮换认证票据、session id、correlation cookie 和 antiforgery token
- ASP.NET Core Identity、CookieAuthentication、SessionMiddleware、DataProtection key ring 与分布式缓存会话的一致性
- TokenValidationParameters、签名算法、kid 选择、密钥轮换、issuer/audience、exp/nbf、clock skew、refresh token 管理
- JWT、cookie、session、remember me、外部登录回调、设备信任和无状态 API 混用时的边界问题
- 登出是否清理客户端 cookie、服务端 session、刷新令牌、服务器缓存、SignalR 连接状态和后台持久会话

## 重点检查

- Cookie flags：HttpOnly、Secure、SameSite 是否正确配置
- 会话固定：登录后是否轮换 Session ID / 认证票据
- JWT 校验：签名算法白名单、exp/nbf/iss/aud 校验、ClockSkew 设置
- 登出清理：Cookie、Session、Refresh Token 是否全部失效
- Refresh Token：存储位置、轮换策略、撤销机制
- 跨域/跨子域 Cookie 共享：Domain 设置过宽导致的会话泄露
- Remember Me / Persistent Cookie：长期票据的安全性与撤销能力
- 滑动过期：SlidingExpiration 是否导致会话永不过期

## 证据引用

- EVID_SESS_COOKIE_FLAGS
- EVID_SESS_TICKET_REGEN_ROTATION
- EVID_SESS_JWT_VERIFY_CLAIMS
- EVID_SESS_LOGOUT_CLEAR

## 枚举规则（强制细化）

- 枚举所有 CookieAuthentication、SessionMiddleware、Identity、JwtBearer、RefreshToken、RememberMe、Persistent Cookie 配置与使用点
- 优先搜索 HttpOnly、SecurePolicy、SameSite、ExpireTimeSpan、SlidingExpiration、SaveTokens、TokenValidationParameters、RefreshToken 表/缓存
- 枚举登录、权限提升、租户切换、2FA 完成、外部登录回调、密码重置后的票据更新路径
- 对每个会话机制记录：票据类型、存储位置、轮换时机、登出清理路径、是否跨子域/跨应用共享

## Barrier 验证矩阵（强制）

按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 三级标准评估：

| 等级 | 检查项 | 通过标准 | 失败降级 |
|------|--------|----------|----------|
| 一级 | 会话/Cookie/JWT 机制存在且实际使用 | CookieAuthentication/SessionMiddleware/JwtBearer 存在且被实际用于认证流程 | BLOCKED → 无会话/Cookie/JWT 使用，专项结束 |
| 二级 | 安全属性缺失或配置错误 | HttpOnly/Secure/SameSite 缺失、TokenValidationParameters 宽松、SlidingExpiration 永不过期 | BLOCKED → 安全属性配置正确，结论降级 |
| 三级 | 轮换/登出清理缺陷可导致会话固定或劫持 | 登录提权后未轮换票据、登出未清理客户端/服务端/Refresh Token | PARTIAL → 仅输出潜在风险与验证步骤 |

## 二阶段判定流程（强制）

- **阶段 1（初筛命中）**：命中 CookieAuthentication/SessionMiddleware/JwtBearer + 安全属性配置 + 轮换/登出路径，输出 `命中ID：M{hash}`。
- **阶段 2（精筛确认）**：
  1. 逆向追踪 登录 → 票据生成 → 传输 → 校验 → 登出清理 链路；
  2. 验证 Cookie flags、TokenValidationParameters、SlidingExpiration 等安全属性配置；
  3. 评估登录提权后票据轮换与登出清理（客户端/服务端/Refresh Token）完整性；
  4. 若三级 Barrier 全部通过 → `确认漏洞`；任一失败 → 按矩阵降级。

## 判定规则与优先级（强制）

1. **确认漏洞**：会话机制使用 + 安全属性缺失 + 轮换/登出清理缺陷可导致利用。输出 `确认漏洞`。
2. **待确认**：会话机制存在但安全属性或轮换/登出证据部分缺失。输出 `待确认`。
3. **误报/无风险**：会话机制安全属性完整（HttpOnly/Secure/SameSite/Strict）、TokenValidationParameters 严格、轮换与登出清理完整。输出 `误报` 并给出判定依据。

## 测试建议与最小触发条件（强制）

- **最小触发条件**：
  - 存在 CookieAuthentication/SessionMiddleware/JwtBearer 使用
  - Cookie flags 缺失或 TokenValidationParameters 宽松
  - 或登录提权后未轮换票据、登出未清理 Refresh Token
- **测试用例建议**：
  - Happy Path：正常登录/登出流程，票据轮换与清理完整
  - 边界/歧义：SameSite=None 跨站请求携带、SlidingExpiration 永不过期、JWT none/HS256 算法混淆、Refresh Token 复用检测缺失
- 每条命中输出追加 `命中ID：M{hash}` 和 `test_id：T{hash}`，用于回溯。

## 证据引用

证据引用：

- EVID_SESS_COOKIE_FLAGS
- EVID_SESS_TICKET_REGEN_ROTATION
- EVID_SESS_JWT_VERIFY_CLAIMS
- EVID_SESS_LOGOUT_CLEAR

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（票据属性确认）**：必须确认 Cookie/JWT/Session 的关键安全属性。
- 🔴 **CHECKPOINT B（轮换与续期确认）**：必须确认登录、提权、租户切换后的票据轮换行为。
- 🔴 **CHECKPOINT C（注销清理确认）**：必须确认客户端与服务端会话均已失效。
- 🛑 **STOP**：若轮换或注销证据不闭合，结论降级为 `⚠️待验证`。

## 失败场景与兜底（if-then）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| 票据属性证据不完整 | 补齐 Cookie/JWT/Session 安全属性配置 | 降级 `⚠️待验证` |
| 登录提权后轮换链未闭合 | 追踪 session/token 轮换执行点 | 不输出“会话安全”强结论 |
| 登出清理链缺失（客户端/服务端） | 补齐 cookie/session/refresh token 撤销证据 | 保守评估并列待补证据 |

🔴 **STOP：任一兜底触发时，禁止输出“无会话风险”。**

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

- 反模式：只看 Cookie flags 就判会话安全。正确做法：同时验证轮换、撤销与登出清理。
- 反模式：忽略 Refresh Token 生命周期。正确做法：核对存储、轮换、撤销与复用检测。
- 反模式：把跨子域共享默认视作可接受。正确做法：按最小作用域限制 Domain/Path。
- 反模式：证据不足宣告“无会话风险”。正确做法：降级 `⚠️待验证`。

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

- vuln_audit/sess_{timestamp}.md
- 可选：vuln_poc/sess_{timestamp}.md（如能构造复现请求、配置验证步骤或环境依赖验证链）
