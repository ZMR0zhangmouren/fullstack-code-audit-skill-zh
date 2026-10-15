---
name: node-auth-audit
description: Node.js 鉴权静态分桶工具。消费 node-route-mapper 产出的 routes 与 middleware_inventory，识别全局中间件覆盖、路由级鉴权、匿名放行与鉴权缺失四桶，输出 100% 覆盖 routes 清单的 auth_mapping。
---

# Node.js Auth Audit

## 共享抓手索引引用

- 本 Skill 的枚举关键字、优先对象与记录口径以 `skills/shared/NODE_AUDIT_GRABBER_INDEX.md` 为单一真源，重点使用其“前置控制抓手”章节。
- 路径与产物命名遵循 `skills/shared/IO_PATH_CONVENTION.md` 中 `node/` 子树约定。
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围。
- 若项目存在 `AuthService`、`PermissionChecker`、`JwtGuard`、`SessionManager` 等二次封装，必须补充到输出的项目内抓手章节。

## 输入依赖

用户提供：

- `node_source_path`：Node.js 项目、仓库根目录或包含 `package.json` 的目录（必需）。
- `node/route_mapping/routes_{timestamp}.md`：上游 node-route-mapper 产出的完整入口清单（必需）。
- `node/route_mapping/middleware_inventory_{timestamp}.md`：上游 node-route-mapper 产出的中间件清单（必需）。
- `node/route_mapping/params_{timestamp}.md`：上游 node-route-mapper 产出的参数结构（可选，用于核对鉴权相关参数来源）。
- `node/stack_detect/stack_detect_{timestamp}.md`：阶段 0 技术栈检出结果（可选，用于选择适配器）。
- `node/design_intent/design_intent_{timestamp}.md`：设计意图摘要（可选，意图层参考：设计中的权限矩阵与租户边界声明，用于补全枚举，禁止作为 EVID 引用源，见 `shared/AUDIT_EXECUTION_COMMON.md` §9）。
- `node/route_mapping/feature_api_map_{timestamp}.md`：功能视图（可选，用于敏感度分级的功能视图规则，见「分桶规则（强制）」节末块；视图层参考禁止作 EVID 引用源，见 `shared/AUDIT_EXECUTION_COMMON.md` §9）。

## 鉴权机制识别

若 `node/design_intent/` 产物存在，优先核对其「权限与租户边界意图」与识别点的差异（差异登记为文档-实现漂移，不直接升级为漏洞结论）。

枚举并归类项目中的鉴权控制点，至少覆盖以下关键字与模式：

| 类别 | 关键字 / 模式 | 识别重点 |
| ---- | ---- | ---- |
| Express 鉴权中间件 | `passport.authenticate`、`express-jwt`、`expressjwt`、`jwt.verify` | 挂载路径、作用域、失败回调、secret/key 来源 |
| Session 鉴权 | `express-session`、`cookie-session` | 全局 / 路由级挂载、Cookie 签名、Session 存储配置 |
| Next.js 鉴权 | `next-auth`、`getServerSession` | API 路由 / Server Action / 页面级覆盖、公开路由配置 |
| NestJS 鉴权装饰器 | `@UseGuards`、`AuthGuard`、`@Public`、`CanActivate` | Controller/Method 级 Guard 覆盖、Public 例外 |
| 自定义命名启发式 | `auth\|login\|token\|guard\|permission\|session` | 项目内封装函数、鉴权工具类、权限校验中间件 |

对每个识别点记录：

- `auth_id`：`A{序号}`，全局唯一。
- `auth_mechanism`：具体关键字或模式名。
- `scope`：`global` / `route` / `module`。
- `covered_route_ids`：覆盖的 `route_id` 列表；全局中间件可写 `*` 并展开实际匹配路由。
- `source_file:line`：声明位置。
- `is_fail_close`：**强制字段**，必须填写 `true` / `false` / `未知`。`true`：未授权请求被拒绝且无法绕过分桶；`false`：鉴权失败可降级放行（存在显式 fallback）；`未知`：无法从代码确认，须落盘 `fail_close_evidence_gap` 说明缺失证据。

## 分桶规则（强制）

将每条 `route_id` 归入以下四桶之一：

| 分桶 | 判定条件 | 记录字段 |
| ---- | ---- | ---- |
| **全局中间件覆盖** | 路由位于 `is_global=true` 且 `is_auth=true` 的中间件挂载路径下 | `auth_id`、中间件名、挂载前缀、作用域证据 |
| **路由级鉴权** | 路由本身或所属 Controller/Module 显式声明 `passport.authenticate`、`express-jwt`、`expressjwt`、`jwt.verify`、session 校验、`@UseGuards`、`AuthGuard` 等 | `auth_id`、鉴权机制、声明位置、覆盖方法 |
| **匿名放行** | 路由显式标注 `@Public`、`AllowAnonymous`、位于公开白名单、或配置为 `unprotected` / `public` 路由 | `auth_id`、放行原因、配置来源、业务必要性说明 |
| **鉴权缺失** | 路由既无全局鉴权中间件覆盖，也无路由级鉴权，且未被标注为匿名放行 | `route_id`、缺失证据、风险等级、建议动作 |

分桶优先级：

1. 先判“匿名放行”（显式公开 > 隐式缺失）。
2. 再判“全局中间件覆盖”。
3. 再判“路由级鉴权”。
4. 其余归入“鉴权缺失”。

**功能视图优先（2026-09-19）**：导出/删除/批量操作/租户管理/凭据类功能端点直接 P0；功能视图未覆盖的端点回退命名/写操作启发式，并在产物中标注分级依据来源（feature_api_map / 启发式）。

## 对账要求（强制）

- 鉴权映射必须 **100% 覆盖** `routes_{timestamp}.md` 中的 `route_id` 清单。
- 对每条 `route_id` 输出一条分桶记录，禁止遗漏。
- 对“非入口/静态资源”类路由（如静态文件、`/health`、`/favicon.ico`、`/_next/static/**` 等）同样落表，并在 `bucket` 旁标注 `non-asset-remark=非入口/静态资源`。
- 输出 `auth_mapping_summary`：
  - `total_routes`：routes 清单总数
  - `global_middleware_count`：全局中间件覆盖数
  - `route_level_count`：路由级鉴权数
  - `anonymous_count`：匿名放行数
  - `missing_count`：鉴权缺失数
  - `coverage_percent`：`(global_middleware_count + route_level_count) / total_routes * 100%`（真实鉴权覆盖率：受鉴权中间件或路由级鉴权保护的路由占比）
  - `classification_completeness`：`(global_middleware_count + route_level_count + anonymous_count + missing_count) / total_routes * 100%`，必须为 100%（分类完备性自检：所有路由均落入四桶，度量分类完备而非鉴权覆盖）
  - `uncovered_route_ids`：空数组为通过；非空则 `auth_mapping_status=BLOCKED`
- 当 `middleware_inventory` 中鉴权中间件 `is_auth=true` 但无法关联到任何 `route_id` 时，写入 `orphan_auth_middleware` 清单并说明原因。

**中间件挂载顺序核查（强制）**：对 `middleware_inventory` 中 `is_auth=true` 的中间件，必须核对挂载顺序——全局中间件在路由注册前 `app.use(...)` 挂载；路由级中间件在具体 route 注册时传入；确认不存在「先注册路由后挂载中间件」导致部分路由绕过鉴权中间件的情形。发现顺序问题写入 `orphan_auth_middleware` 或分桶记录的 notes 列。

## 输出

按 `skills/shared/IO_PATH_CONVENTION.md` 中 Node.js 产物路径落盘：

| 产物 | 物理路径 |
| ---- | ---- |
| 鉴权静态分桶 | `node/auth_audit/auth_mapping_{timestamp}.md` |
| 阶段索引 | `node/auth_audit/index_{timestamp}.md` |
| 空结果说明（如适用） | `node/auth_audit/empty_result_{timestamp}.md` |

### auth_mapping_{timestamp}.md 最小字段

- `auth_id`：鉴权控制点唯一 ID
- `route_id`：关联的 `R{序号}`，多对多关系可展开多行
- `bucket`：全局中间件覆盖 / 路由级鉴权 / 匿名放行 / 鉴权缺失
- `auth_mechanism`：识别的关键字或模式
- `scope`：global / route / module
- `source_file:line`
- `non-asset-remark`：空或“非入口/静态资源”
- `confidence`：HIGH / MEDIUM / LOW
- `next_action`：补测、补 trace、或无需动作
- `notes`：顺序问题/挂载核查发现记录（挂载顺序核查发现时填写）

### 输出前自检

- [ ] 所有 `route_id` 均已落表，无遗漏。
- [ ] 四桶分类无歧义，匿名放行有显式证据。
- [ ] `classification_completeness = 100%`（四桶求和自检，度量分类完备而非鉴权覆盖）。
- [ ] `coverage_percent` 按真实鉴权口径计算，分子仅含 `global_middleware_count + route_level_count`。
- [ ] `uncovered_route_ids` 为空。
- [ ] 自定义命名启发式（`auth|login|token|guard|permission|session`）已纳入项目内抓手清单。

## 机制扩展：账号枚举（2026-09-14 台账轮）

### 机制描述与边界

不可信登录请求 → 认证错误响应 → 账号存在性/认证状态/错误类型可区分信号。攻击者通过对比成功、失败、账号不存在三种路径在状态码、响应体、时序上的差异，推断账号是否存在、是否锁定、认证方式等状态。

台账边界（逐字）：纳入既有认证审计错误响应一致性维度，不新建枚举 Skill；不属于本扩展：认证绕过/口令爆破（归既有认证维度）。

### 重点检查与枚举抓手

至少覆盖以下四类枚举面，每命中记录：文件、行号、端点、差异信号类型（状态码/响应体/时序）：

- **登录端点错误响应分支**：自研登录路由是否按「用户不存在」/「密码错误」/「账号锁定」返回差异化响应体（如 `res.status(401).json({ error: "user_not_found" })` vs `{ error: "wrong_password" }`）或差异化状态码；passport `localStrategy` 回调中 `done(null, false, { message })` 的分支 message 是否泄露账号状态。
- **时序均衡缺失**：`bcrypt.compare` 是否在用户不存在时短路跳过，导致不存在账号响应明显更快；JWT 签发时机差异（用户不存在时是否额外延迟）是否形成可观测时间差。
- **找回密码流程响应差异**：按邮箱查询用户返回 null 与发送重置邮件两条路径的响应是否一致；「该邮箱未注册」类提示是否直接暴露存在性。
- **注册流程存在性提示**：用户名/邮箱唯一性校验是否返回「该用户名已被占用」等可区分提示，且提示颗粒度是否到具体字段值。

### 验证矩阵

| Barrier 类型 | 验证动作 | 判定标准 |
|-------------|---------|---------|
| **响应一致性统一** | 分别提交 正确口令+存在账号 / 错误口令+存在账号 / 任意口令+不存在账号，比对三次响应的状态码与响应体指纹 | 三路径指纹完全一致 → ✅ 安全；任一可区分 → 🔴 高危待确认 |
| **时序均衡** | 对存在与不存在账号各测响应耗时分布，确认不存在账号是否走同代价路径（bcrypt 校验不短路） | 恒定时序或统一代价 → ✅ 安全；不存在账号明显更快 → ⚠️ 待确认 |
| **错误信息泛化** | 检查错误消息与错误码是否区分「用户不存在」/「密码错误」/「账号锁定」 | 统一为泛化文案（如「用户名或密码错误」）且无状态码区分 → ✅ 安全；文案或码值可区分 → 🔴 高危待确认 |

🔴 **STOP：任一 barrier 验证为 `silent-fallback` 或 `fail-open` 时，禁止将结论标记为「已确认安全」或「误报」。**

### 判定规则

确认需同时闭合以下三个 EVID，缺一不可：

1. **端点面闭合**：登录/找回/注册枚举面证据（`EVID_NODE_AUTH_ENUM_ENDPOINT_SURFACE`）。
2. **可观察差异闭合**：成功/失败/不存在账号间可观察差异（状态码/响应体/时序至少一项）证据（`EVID_NODE_AUTH_ENUM_OBSERVABLE_DIFF`）。
3. **影响闭合**：账号存在性或认证状态可被推断的影响闭合证据（`EVID_NODE_AUTH_ENUM_IMPACT_CONFIRM`）。

🔴 **确认阈值（台账原文）：仅理论差异不得确认——必须证明可观察差异（响应体/状态码/时序至少一项）。**

已统一响应且时序均衡为误报。

### 测试建议

- **正向**：以不存在账号与错误口令各发一次登录请求，确认响应差异（状态码/响应体/时序至少一项）可观察。
- **负向**：统一响应 + 时序均衡后，两路径不可区分。
- **回归**：新增认证端点（含找回密码、注册、2FA 校验）时，对响应一致性做复核。

### 证据引用

- `EVID_NODE_AUTH_ENUM_ENDPOINT_SURFACE`：登录/找回/注册端点枚举面证据
- `EVID_NODE_AUTH_ENUM_OBSERVABLE_DIFF`：成功/失败/不存在账号间可观察差异（状态码/响应体/时序至少一项）证据
- `EVID_NODE_AUTH_ENUM_IMPACT_CONFIRM`：账号存在性或认证状态可被推断的影响闭合证据
