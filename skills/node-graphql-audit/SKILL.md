---
name: node-graphql-audit
description: Node.js GraphQL 框架专项审计工具。针对 GraphQL schema 与 resolver 参数来源、内省开关、深度/复杂度限制、resolver 内鉴权、错误格式化与运行时配置进行白盒审计。
---

# GraphQL 框架专项审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与 GraphQL 相关的 schema/type 定义、resolver 参数来源（context/args）、内省与 playground 开关、深度/复杂度限制、错误格式化、鉴权守卫配置抓手
- 若项目存在 schema 拼接（schema stitching/联邦 gateway）、resolver 工厂、统一鉴权包装器（自定义 directive/`graphql-shield` 规则），必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐 GraphQL 入口端点与 `route_id`，本专项入口通常收敛为 `/graphql` 单端点）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（用于确认 `/graphql` 端点前置中间件鉴权覆盖顺序）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（本专项核心输入：对齐匿名入口、P0/P1 分桶与 resolver 级鉴权覆盖范围）
- 可选：`node/route_tracer/{route_id}/trace_{timestamp}.md` 与 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md`（用于将 resolver 参数到 sink 的数据流与具体入口交叉引用）
- 可选：`node/vuln_audit/*_{timestamp}.md`（用于与 nosql/expr/cmd/ssrf 等漏洞专项互相印证，resolver 内注入面）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于对齐 BFF 转发或前后端同构参数来源）

## 重点检查

- schema 定义与 resolver 参数来源：resolver 的 `args`/`context` 解析面，参数直通查询/命令执行（resolver 内注入，联调 node-nosql/node-expr 专项）
- 内省（introspection）开关：生产环境未关闭 introspection → schema 结构与内部字段名泄露（攻击面扩大）
- 深度/复杂度限制缺失：`graphql-depth-limit`/`maxDepth`/`complexity` 未配置 → 深层嵌套/批量查询/别名滥用 DoS
- resolver 内鉴权缺失：字段级守卫（`graphql-shield`/自定义 directive）未覆盖部分 query/mutation，或鉴权仅依赖前端隐藏字段
- 错误堆栈泄露：`formatError`/`formattedErrors` 未净化，错误响应含堆栈与内部路径（联调 `EVID_NODE_CFG_ERR_HANDLER`）
- `graphql-playground`/GraphiQL 在生产开启 → 交互式查询面暴露
- 批量查询与别名滥用：`__typename` 注入、批量字段别名放大服务端成本（缓存绕过）

## 枚举规则（强制细化）

### 1. 框架边界层

- 枚举入口定义方式：`GraphQLModule.forRoot`（@nestjs/graphql）/`ApolloServer`/`express-graphql`/`mercurius`（Fastify）挂载点与端点路径、网关/联邦子图边界（`@key`/`@external` 指令）
- 枚举 schema 定义：SDL 文件或 code-first（`@ObjectType`/`@Field`/`@Resolver`）中的 type/query/mutation 定义、自定义 directive（`@auth`/`@requireRole` 等）挂载面
- 枚举 resolver 参数来源：`args` 提取、`context`（`req`/`user`/`db`）解析、`@Parent`/`@Info` 字段选择面，参数直通 sink 的路径
- 识别请求生命周期边界：HTTP 请求 → GraphQL 解析（parse/validate/execute）→ resolver 链（字段级按深度展开）→ 响应
- 识别批处理面：`batch`/`batching` 配置、alias 与重复字段选择（解析器重复执行放大面）

### 2. 运行时配置层

- 枚举 introspection 配置：`introspection: true/false` 开关、环境分支（开发开/生产关）、playground/GraphiQL 的 `playground: true` 配置
- 枚举深度/复杂度限制：`validationRules`（`graphql-depth-limit`、`graphql-validation-complexity`）、`maxDepth`/`maxComplexity`/`requestDidStart` 插件、`maxQueryDepth`（Mercurius）
- 枚举错误格式化：`formatError`/`formattedErrors`/`customFormatErrorFn` 是否净化堆栈与内部路径、`includeStacktraceInErrorResponses` 开关（Apollo）
- 枚举解析器成本控制：默认字段解析器（`defaultFieldResolver`）、resolver 内 N+1 查询（无 DataLoader）的放大面
- 枚举环境变量读取点：schema 路径/端点配置、`process.env` 敏感项、运行时构建分支

### 3. 前置控制面层

- 枚举 resolver 级鉴权覆盖：`graphql-shield` 规则（`rule`/`shield` 中间件）、自定义 auth directive、`@UseGuards`（nestjs/graphql）、context 内 `user` 注入来源（JWT 校验点）
- 识别字段级鉴权缺失：比对 schema 全部 query/mutation/字段与鉴权规则覆盖，标记未覆盖的 resolver 与嵌套字段
- 枚举解析前拦截面：Apollo 插件（`requestDidStart`/`didResolveOperation`）、HTTP 层中间件鉴权（`/graphql` 端点前置 auth）与 resolver 内鉴权的叠加
- 枚举速率限制与请求大小限制：`graphql-rate-limit`/throttler 配置、单请求大小限制、持久化查询（persisted queries）白名单

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| 内省开关 | `introspection: false`（生产） | 检查 introspection/playground 配置的环境分支与生产值 | 生产关闭且开发/生产配置隔离 → ✅ 安全；生产开启 introspection 或 playground → 🔴 高危 |
| 深度限制 | `validationRules: [depthLimit(10)]` | 检查是否注册 depth/complexity 校验规则及阈值，比对 schema 实际嵌套深度 | 显式深度限制且阈值合理 → ✅ 安全；缺失或阈值过大 → ⚠️ 待确认（DoS 面） |
| resolver 鉴权 | `graphql-shield` shield 中间件 / `@UseGuards(GqlAuthGuard)` | 比对 schema 全部 query/mutation/字段与鉴权规则覆盖，含嵌套字段与动态 schema | 全部 resolver fail-close → ✅ 安全；存在可达的无鉴权 resolver/字段 → 🔴 高危 |
| 错误格式化 | `formatError: (err) => sanitized` | 检查错误格式化是否净化堆栈/内部路径、`includeStacktraceInErrorResponses` 是否关闭 | 自定义格式化且净化 → ✅ 安全；默认输出堆栈/内部路径 → 🔴 泄露（fail-open） |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认风险候选`：框架配置或控制面缺失可能导致外部输入绕过、权限扩大或敏感信息暴露
- `待确认`：上下文显示可疑模式，但入口覆盖范围、barrier 行为或调用链不清晰
- `误报`：配置已显式启用 fail-close，或风险点已被其他控制面覆盖

### 阶段二：强制追证

若阶段一为「待确认」，必须继续向下追至少一跳调用链或下游解析器，直到满足以下任一条件：

- 找到框架控制面与具体入口/sink 发生关联的证据 → `确认风险`
- 找到固定白名单映射 / fail-close 证据 → `误报`
- 仍缺少关键调用链 → 保持 `待确认`，但必须说明缺失哪一跳

**fail-close 语义**：对 barrier、白名单、校验器、过滤器必须以失败模式评估。未知/非法输入必须抛异常、返回空、拒绝执行或日志告警，绝不能透传原始值；任何 silent-fallback 或 fail-open 行为均视为高危。

## 判定规则（强制细化）

### 已确认

- `EVID_NODE_CFG_SECURITY_SWITCH` 显示生产环境 `introspection: true` 或 playground/GraphiQL 开启，schema 结构可被外部枚举
- `EVID_NODE_CFG_RUNTIME_SETTING` 显示 depth/complexity 限制未配置，且 schema 存在深层嵌套/批量查询放大面（DoS 候选）
- `EVID_NODE_CFG_ERR_HANDLER` 显示 `formatError`/`formattedErrors` 未净化堆栈与内部路径，错误响应可被外部触发并读取
- `EVID_NODE_CFG_MIDDLEWARE_ORDER` 显示 resolver 级鉴权规则仅部分 query/mutation 挂载，存在可达的无鉴权 resolver/嵌套字段
- resolver `args` 直通查询/命令构造且无净化 → 联调 node-nosql（`EVID_NODE_NOSQL_RAW_OBJECT_PASS`/`EVID_NODE_NOSQL_OPERATOR_INJECTION`）或 node-cmd 确认注入（`EVID_NODE_CMD_USER_PARAM_TO_CMD`）

### ⚠️待验证

- 深度/复杂度限制缺失是否可被实际 DoS 取决于 schema 结构与解析器成本，需结合服务端资源确认（`EVID_NODE_CFG_RUNTIME_SETTING`）
- 鉴权缺失的 resolver 是否可被外部调用取决于 schema 拼接/联邦边界与 HTTP 层前置鉴权，需确认前置控制面
- 错误堆栈泄露依赖运行时 `NODE_ENV` 与框架版本默认行为，静态无法确认部署环境
- 批量查询/别名滥用放大面依赖解析器实现（N+1 查询），需 trace 到数据访问层确认

### 误报

- 生产配置 `introspection: false` 且 playground 关闭，开发/生产配置隔离明确
- `validationRules` 已注册 depth 与 complexity 限制且阈值与 schema 嵌套深度匹配
- resolver 鉴权规则覆盖全部 query/mutation/嵌套字段且 fail-close（未鉴权直接拒绝）
- `formatError` 已自定义且响应净化（无堆栈/内部路径），`includeStacktraceInErrorResponses` 关闭

## 测试建议（强制）

### 正向测试

- 生产环境发送 introspection 查询 → 应被拒绝或返回空 schema
- 构造超深嵌套查询/超大批量别名查询 → 应被深度/复杂度限制拒绝而非进入 resolver 执行
- 无鉴权直接查询未覆盖 resolver 的字段 → 应被拒绝（401/403）
- 触发 resolver 异常 → 响应应为净化错误，不包含堆栈/内部路径
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 合法查询携带有效 token 正常返回，schema 内全部授权字段可用
- 正常深度范围内的嵌套查询可用，无误拒
- 生产模式（`NODE_ENV=production`）下错误响应不泄露堆栈

### 回归测试

- schema 新增 query/mutation/字段后必须纳入鉴权规则清单后复测
- introspection/深度限制配置变更后重验开关与限制面
- 错误格式化改动后复测堆栈泄露面

## 证据引用

- `EVID_NODE_CFG_SECURITY_SWITCH`（introspection/playground 开关与安全配置证据）
- `EVID_NODE_CFG_RUNTIME_SETTING`（深度/复杂度限制与运行时配置证据）
- `EVID_NODE_CFG_ERR_HANDLER`（formattedErrors 堆栈泄露证据）
- `EVID_NODE_CFG_MIDDLEWARE_ORDER`（resolver 鉴权规则覆盖与执行顺序证据）
- `EVID_NODE_NOSQL_RAW_OBJECT_PASS` 与 `EVID_NODE_NOSQL_OPERATOR_INJECTION`（resolver 参数直通查询结构，联调 node-nosql-audit）
- `EVID_NODE_CMD_USER_PARAM_TO_CMD`（resolver 参数进入命令构造，联调 node-cmd-audit）

## 输出

- `node/framework_audit/graphql_{timestamp}.md`
- 必须写明：入口端点与框架选型（Apollo/express-graphql/mercurius/nestjs-graphql）、schema 与 resolver 清单、resolver 参数来源与净化状态、introspection/playground 开关、深度/复杂度限制、resolver 鉴权覆盖范围与未覆盖字段、错误格式化行为
- 必须写明环境差异：开发/生产配置分支（introspection/playground）、`NODE_ENV` 分支、schema 拼接/联邦部署差异
- 消费关系：影响漏洞强结论时必须显式写明如何被 `node/route_tracer`、各 `node-vuln-audit` 专项（nosql/cmd/ssrf/expr 等）与 `node-audit-pipeline` 消费
