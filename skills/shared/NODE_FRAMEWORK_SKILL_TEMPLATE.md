# Node.js 框架专项 Skill 模板

本模板用于新增 node-{framework}-audit 类框架专项 Skill，供 P2 Node.js 全栈扩展各框架专项起稿使用。

## 使用说明

- 将 {framework} 替换为具体框架或运行时子域（如 express、nestjs、nextjs、koa、fastify、nuxt 等）
- 框架专项默认用于描述 框架边界、运行时控制面、宿主差异、组件暴露面，而不是替代漏洞专项
- 默认接入 shared/NODE_AUDIT_GRABBER_INDEX.md、shared/NODE_SINK_REFERENCE.md、shared/SEVERITY_RATING.md、shared/IO_PATH_CONVENTION.md
- **默认遵循 shared/DOTNET_AUDIT_EXECUTION_STANDARD.md 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）；该标准栈无关，Node.js 侧直接引用**
- 必须显式写出 `## 输入依赖`，不要把 `node_source_path`、`node/route_mapping/*`、`node/auth_audit/*`、`node/route_tracer/*` 的关系留成隐含约定
- 框架专项默认以 `node_source_path` 为必需输入；若已存在 `node-route-mapper` 产物，应把 `node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md` 写为可选输入，用于对齐入口、参数绑定与 `route_id`
- 若框架专项涉及匿名入口、P0/P1 分桶、授权元数据或资源归属边界，应把 `node/auth_audit/auth_mapping_{timestamp}.md` 写为可选输入
- 若框架专项需要将中间件、组件、控制面风险与具体入口、副作用链做交叉引用，应把 `node/route_tracer/{route_id}/trace_{timestamp}.md` 与 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` 写为可选输入
- 若框架专项涉及 SSR、BFF 转发或前后端同构逻辑，应把 `cross/api_contract_map_{timestamp}.md` 写为可选输入
- 如果该框架专项会影响漏洞强结论，必须显式写明其如何被 route_tracer、vuln_audit 和 node-audit-pipeline 消费
- 若该框架专项需要新增 EVID_NODE_* 或新的 shared 抓手，应先更新 shared 再落 Skill

## 模板

```md
---
name: node-{framework}-audit
description: Node.js {framework} 框架专项审计工具。针对 ... 的框架边界、运行时配置与控制面进行白盒审计。
---

# {framework} 框架专项审计

## 共享抓手索引引用

- 默认以 shared/NODE_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/NODE_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 shared/DOTNET_AUDIT_EXECUTION_STANDARD.md 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 shared/SEVERITY_RATING.md 作为分级与编号规范
- 默认以 shared/IO_PATH_CONVENTION.md 作为产物路径与命名规范
- 枚举时至少覆盖与 {framework} 相关的入口定义、绑定转换、前置控制、敏感操作、安全配置抓手
- 若项目存在框架二次封装、统一扩展方法、平台基座或宿主包装层，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（如已由 `node-route-mapper` 生成，用于对齐入口、参数绑定与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（用于确认中间件覆盖顺序与短路条件）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（如需对齐匿名入口、P0/P1 分桶、授权元数据或资源归属边界）
- 可选：`node/route_tracer/{route_id}/trace_{timestamp}.md` 与 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md`（如需将框架控制面与具体入口、副作用链做交叉引用）
- 可选：`cross/api_contract_map_{timestamp}.md`（如需对齐 SSR、BFF 转发或前后端同构参数来源）

## 重点检查

- ...

## 枚举规则（强制细化）

### 1. 框架边界层

- 识别 {framework} 的入口定义方式（Middleware 注册、路由挂载、装饰器、文件约定等）
- 识别全局/路由级中间件链（app.use、router.use、addHook、中间件顺序）
- 识别请求生命周期边界（req → middleware → handler → response）
- 识别框架默认提供的静态目录、错误处理、404 处理、全局异常捕获

### 2. 运行时配置层

- 识别运行时环境变量读取点（process.env、dotenv、.env）
- 识别安全头配置（helmet、CORS、CSP、HSTS、X-Frame-Options）
- 识别会话与 Cookie 配置（session store、cookie-parser、csrf、SameSite、secure、httpOnly）
- 识别序列化/反序列化配置（body-parser、express.json、fastify 默认 schema、NestJS ValidationPipe）
- 识别 SSR 渲染配置（Next.js/Nuxt 渲染模式、getServerSideProps、server component、边缘运行时）

### 3. 前置控制面层

- 识别鉴权覆盖范围（passport、express-jwt、jwt.verify、@UseGuards、AuthGuard、@Public）
- 识别 Guard/Interceptor/Filter 执行顺序与短路条件
- 识别权限/角色校验装饰器与元数据
- 识别速率限制、请求大小限制、文件上传限制配置

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| ... | ... | ... | ... |

## 二阶段判定（强制）

本专项遵循 shared/DOTNET_AUDIT_EXECUTION_STANDARD.md 的二阶段判定流程：

> 通用执行标准以 shared/AUDIT_EXECUTION_COMMON.md 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

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

- ...

### ⚠️待验证

- ...

### 误报

- ...

## 测试建议（强制）

### 正向测试

- ...

### 负向测试

- ...

### 回归测试

- ...

## 证据引用

- EVID_NODE_...

## 输出

- `node/framework_audit/{framework}_{timestamp}.md`
- 必须写明入口类型、框架边界、运行时配置、环境差异、与其他专项的联动关系
- 如果该框架专项会影响漏洞强结论，必须显式写明其如何被 `node/route_tracer`、各 `node-vuln-audit` 专项和 `node-audit-pipeline` 消费
```

## 最低验收要求

- 名称、description、职责边界清晰
- 已引用 shared/NODE_AUDIT_GRABBER_INDEX.md、shared/NODE_SINK_REFERENCE.md、shared/DOTNET_AUDIT_EXECUTION_STANDARD.md、shared/SEVERITY_RATING.md、shared/IO_PATH_CONVENTION.md
- 已具备完整十层结构：共享抓手索引引用 + 输入依赖 + 重点检查 + 枚举规则（强制细化）+ Barrier 验证矩阵（强制）+ 二阶段判定（强制）+ 判定规则（强制细化）+ 测试建议（强制）+ 证据引用 + 输出
- 已保留 dotnet 版三层结构：框架边界层 / 运行时配置层 / 前置控制面层
- 已将 .NET 概念替换为 Node.js 对应物（Middleware 链、Guard/Interceptor、helmet/CORS、session store、SSR 配置）
- 已说明证据引用口径（含 EVID_NODE_* 占位或真实证据点）
- 已说明与 node/route_tracer / node/vuln_audit / pipeline / cross 端的关系
- 已写明该框架专项如何被 route_tracer、vuln_audit 和 pipeline 消费
- Barrier 验证矩阵列头严格为 `| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |`
- 输出路径符合 shared/IO_PATH_CONVENTION.md，且明确写为 `node/framework_audit/{framework}_{timestamp}.md`
- 能与现有 framework 专项区分边界，不产生大面积重复职责
