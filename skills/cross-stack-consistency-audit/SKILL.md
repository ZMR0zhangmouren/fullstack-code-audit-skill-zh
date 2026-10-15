---
name: cross-stack-consistency-audit
description: 两侧配置一致性审计 Skill。对 node 侧与 dotnet 侧的安全配置做五组对账（JWT/Cookie/CORS/CSRF/错误处理），差异即漏洞线索，输出 cross/consistency_findings_{timestamp}.md 供全栈收尾一致性核对消费。
---

# Cross-Stack Consistency Audit

## 共享抓手索引引用

本 Skill 的产物路径以 `skills/shared/IO_PATH_CONVENTION.md` 为单一真源（`consistency_findings_{timestamp}.md` 已登记于 :253）。证据点引用以 `skills/shared/EVIDENCE_POINT_IDS.md` 为口径：node 侧引用 `EVID_NODE_CFG_*` / `EVID_NODE_SESS_*`，dotnet 侧引用既有 `EVID_CFG_*` / `EVID_AUTH_*`——跨栈引用两侧各自证据点是本 Skill 的正当用途（两侧各自取证后对账）。

## 输入依赖

| 输入 | 路径 | 必需性 |
| ---- | ---- | ---- |
| dotnet 侧认证审计产物 | `{output_root}/dotnet/auth_audit/`（或等效） | 必需（JWT/CSRF 对账） |
| dotnet 侧配置审计产物 | `{output_root}/dotnet/config_audit/`（或等效） | 必需（Cookie/CORS/错误处理对账） |
| node 侧认证审计产物 | `{output_root}/node/auth_audit/`（或等效） | 必需（JWT/CSRF 对账） |
| node 侧配置审计产物 | `{output_root}/node/config_audit/`（或等效） | 必需（Cookie/CORS/错误处理对账） |
| 技术栈检出 | `{output_root}/node/stack_detect/stack_detect_{timestamp}.md` | 必需（确定前端部署形态与 SSR 面，CORS/CSRF 对账依赖） |
| 契约对账三桶表 | `{output_root}/cross/api_contract_map_{timestamp}.md` | 可选（BFF 是否透传/中转请求的佐证） |

- 前置约束：任一侧审计产物缺失时，对应该侧的对账项结论一律 `待验证（一侧证据缺失）`，禁止单侧推定差异成立；两侧产物均缺失的对账项在产物中声明 `audit_side_missing=both` 并整组挂起。

## 对账项（五组，强制）

差异即漏洞线索，逐组输出对比表。对比表骨架固定为：**检查点列 + node 侧取证指引列 + dotnet 侧取证指引列**。

| 对账项 | 检查点 | node 侧取证指引 | dotnet 侧取证指引 |
| ---- | ---- | ---- | ---- |
| JWT | 签发侧 vs 校验侧的密钥来源一致性；算法钉死（禁止 `alg:none` / 算法混淆）；过期（exp）与受众（aud）校验是否一致 | `EVID_NODE_SESS_JWT_SIGN_VERIFY_CONFIG`（jwt.sign/jwt.verify 配置）、`EVID_NODE_SESS_JWT_ALG_PINNED`（算法钉死）、`EVID_NODE_SESS_SECRET_SOURCE`（密钥来源） | `EVID_AUTH_TOKEN_DECODE_JUDGMENT`（票据解析判断）、`EVID_CFG_RUNTIME_SETTING_CODE`、`EVID_CFG_CONFIG_LOCATION`（密钥配置位置与来源） |
| Cookie | 两侧 Set-Cookie 的 HttpOnly / Secure / SameSite / Domain / Path 是否互相削弱（如 BFF 转写 Cookie 丢失 flags） | `EVID_NODE_SESS_COOKIE_FLAGS`（Cookie flags 证据） | `EVID_CFG_SECURITY_SWITCH_EVIDENCE` 及框架 Cookie 配置产物 |
| CORS | 后端 origin 白名单 vs 前端真实部署域名；`Access-Control-Allow-Credentials` 与通配符组合（**明确禁止组合**：`Allow-Credentials: true` + `*` 通配） | `EVID_NODE_CFG_SECURITY_SWITCH`（CORS 通配+credentials 证据） | `EVID_CFG_SECURITY_SWITCH_EVIDENCE`（dotnet CORS 策略配置） |
| CSRF | BFF 是否存在 token 中转；两侧 SameSite 依赖是否一致；csurf 弃用替代缺失 | `EVID_NODE_CFG_MIDDLEWARE_ORDER`（中间件顺序与短路条件）、csurf/csrf 库使用情况 | `EVID_AUTH_PERMISSION_CHECK_EXEC`、dotnet 侧 CSRF/防伪令牌配置产物 |
| 错误处理 | 两侧错误响应是否泄露堆栈 / 内部路径 / 版本指纹 | `EVID_NODE_CFG_ERR_HANDLER`（全局异常捕获与错误响应泄露） | `EVID_CFG_IMPACT_ASSOCIATION`（配置影响点关联，含错误处理开关） |

对账语义：**一致性差异 ≠ 必然漏洞**，差异仅为漏洞线索；是否成立须结合入口可达性（该配置路径是否存在可达攻击面）在 `风险影响` 字段中论证。

## 执行步骤

按对账项逐组执行（五组均需产出对比表，禁止跳组）：

1. **准备工作**：确认两侧审计产物齐备；从 `stack_detect` 确认前端部署形态（纯 SPA / SSR / BFF）与真实部署域名来源（配置文件或部署证据），作为 CORS/CSRF 对账的参照系。
2. **JWT 对账**：确定实际签发方（node 或 dotnet）；对比两侧 `密钥来源`（硬编码 / 环境变量 / 证书）与算法钉死策略（`alg:none` 拒绝、算法白名单）；对比 exp/aud 校验参数（缺失或放宽的一侧即线索）。
3. **Cookie 对账**：对比两侧 Set-Cookie 的 HttpOnly/Secure/SameSite/Domain/Path 设置；重点检查 BFF 转写/透传场景下 flags 是否丢失（如 dotnet 侧设置了 Secure 而 BFF 重设时未携带）。
4. **CORS 对账**：取后端实际生效的 origin 白名单 vs 前端真实部署域名（含 devServer proxy 展开）；检查 `Allow-Credentials` 与通配符组合是否落入明确禁止组合。
5. **CSRF 对账**：确认 BFF 是否存在 CSRF token 中转（接收前端 token 转发给后端，或依赖会话 Cookie 直传）；对比两侧 SameSite 依赖是否一致（一侧依赖 SameSite=Strict 而另一侧为 Lax 即削弱）；csurf 弃用后替代方案是否缺失（`double-submit` / 自定义中间件 / SameSite+自定义头）。
6. **错误处理对账**：对比两侧错误响应形态——堆栈跟踪、内部物理路径、框架版本指纹是否暴露；异常处理器覆盖范围。
7. **汇总登记**：逐组将对比表结论登记到 `cross/consistency_findings_{timestamp}.md`，每条差异生成 `CONS-{n}`。

## 判定规则

三态判定（对每条 `CONS-{n}` 差异线索）：

| 结论 | 条件 |
| ---- | ---- |
| `已确认差异（两侧证据明确且差异成立）` | 两侧证据齐全（双栈审计产物均落盘），差异客观成立，且结合入口可达性可论证其构成风险 |
| `待验证（一侧证据缺失）` | 任一侧审计产物缺失、配置取值无法确认、或差异是否成立需动态复核 |
| `误报（两侧配置一致或差异有防护抵消）` | 两侧配置一致；或差异虽存在但有防护抵消（如 CORS 白名单虽不含前端域名但同源部署无跨源面、Cookie flags 缺失但有其他层防护） |

判定语义（强制）：

- 「差异即漏洞线索」仅代表该差异**值得登记与深挖**，不得自动升级为漏洞结论；漏洞级别结论须回引对应栈漏洞专项证据。
- 防护抵消必须引用证据（防护存在的位置与配置证据），禁止无证据推定抵消。
- 三态均需在产物中留痕，`待验证` 项不得静默删除。

### CONS-{n} → 跨端利用链联动规则

- 三态中的「差异（需修复）」类 CONS-{n} 自动进入跨端链候选池：差异涉及鉴权（JWT/cookie 生命周期不一致）、CORS（允许源与凭据策略不一致）、CSRF（防护双侧不对称）时，必须评估能否构成跨端利用链（前端伪造 → 后端接受）。
- 联动输出：在 `cross/exploit_chain/cross_stack_exploit_chains_{timestamp}.md` 中为每条联动候选链标注 `consistency_clue=CONS-{n}`，可行性判定与 T2-5 正式产物一致。
- 联动门槛：单条 CONS-{n} 不足以闭合链路时，记 `clue_open` 进待补证风险池，禁止直接给「确认可行」。

## 证据引用

| 证据点 | 侧 | 用途 |
| ---- | ---- | ---- |
| `EVID_NODE_CFG_SECURITY_SWITCH` | node | 安全开关/默认配置（helmet、CORS 通配+credentials） |
| `EVID_NODE_CFG_RUNTIME_SETTING` | node | 运行时配置（process.env、dotenv、.env 泄露） |
| `EVID_NODE_CFG_MIDDLEWARE_ORDER` | node | 中间件/Guard 顺序与短路条件 |
| `EVID_NODE_CFG_SSR_MODE` | node | SSR/同构渲染模式（CORS 同源判定辅助） |
| `EVID_NODE_CFG_ERR_HANDLER` | node | 错误处理与堆栈泄露证据 |
| `EVID_NODE_SESS_JWT_*`、`EVID_NODE_SESS_COOKIE_FLAGS` | node | JWT 配置与 Cookie flags 证据 |
| `EVID_CFG_CONFIG_LOCATION` / `EVID_CFG_RUNTIME_SETTING_CODE` / `EVID_CFG_IMPACT_ASSOCIATION` / `EVID_CFG_SECURITY_SWITCH_EVIDENCE` | dotnet | 配置位置、运行时设置、影响关联、安全开关证据 |
| `EVID_AUTH_*`（`EVID_AUTH_TOKEN_DECODE_JUDGMENT` 等） | dotnet | 认证票据解析与权限检查证据 |

引用 `EVID_NODE_CFG_*` 前确认其已在 `skills/shared/EVIDENCE_POINT_IDS.md` NODE 命名空间 CFG 分组登记（SECURITY_SWITCH / RUNTIME_SETTING / MIDDLEWARE_ORDER / SSR_MODE / ERR_HANDLER 均已登记）。

## 输出

按 `skills/shared/IO_PATH_CONVENTION.md`（:253）落盘 `cross/consistency_findings_{timestamp}.md`，字段：

| 字段 | 说明 |
| ---- | ---- |
| `finding_id` | `CONS-{n}`，对账线索唯一 ID |
| 对账项 | `JWT` / `Cookie` / `CORS` / `CSRF` / `错误处理` 之一 |
| node 侧证据 | 对应 `EVID_NODE_*` 或 node 审计产物引用（路径:行号） |
| dotnet 侧证据 | 对应 `EVID_CFG_*` / `EVID_AUTH_*` 或 dotnet 审计产物引用（路径:行号） |
| 差异描述 | 两侧取值/配置差异的客观描述 |
| 风险影响 | 结合入口可达性的风险论证（差异 ≠ 必然漏洞） |
| 结论三态 | `已确认差异` / `待验证` / `误报` |

产物结构（强制）：对账范围声明（两侧产物时间戳与来源）、五组对比表（逐组）、`CONS-{n}` 明细、三态汇总计数、与 fullstack 收尾的关系声明。

与 fullstack 收尾双保险的关系：本 Skill 由 fullstack 阶段 6（跨端关联）调用；其输出 `cross/consistency_findings_{timestamp}.md` 作为全栈层 `coverage_consistency_check` 的**补充输入**，不作为其替代——consistency_check 的门禁判定、BLOCKED 联动与最终报告对账仍按既有收尾双保险流程执行。
