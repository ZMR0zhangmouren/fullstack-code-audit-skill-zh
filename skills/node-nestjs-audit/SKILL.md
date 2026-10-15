---
name: node-nestjs-audit
description: Node.js NestJS 框架专项审计工具。针对 NestJS 装饰器路由与参数绑定、Guard/Interceptor/Pipe/Filter 管线、ValidationPipe 配置、模块注入边界与运行时配置进行白盒审计。
---

# NestJS 框架专项审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与 NestJS 相关的入口定义（`@Controller`/`@Get` 等装饰器路由）、参数绑定（`@Body`/`@Query`/`@Param`）、Guard/Interceptor/Pipe/Filter 管线、ValidationPipe 配置、模块注入与全局配置抓手
- 若项目存在统一装饰器封装、基类 Controller、动态注册模块（`forRoot`/`forFeature`）、全局 Guard/Pipe 工厂，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（本专项核心输入：对齐装饰器路由入口与 `@Param`/`@Query`/`@Body` 参数绑定及 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（用于确认中间件/Guard 覆盖顺序与短路条件）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于对齐匿名入口、P0/P1 分桶与 Guard 覆盖范围）
- 可选：`node/route_tracer/{route_id}/trace_{timestamp}.md` 与 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md`（用于将参数绑定风险与具体入口、副作用链交叉引用）
- 可选：`node/vuln_audit/*_{timestamp}.md`（用于与 nosql/cmd/upload/xss 等漏洞专项互相印证）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于对齐 BFF 转发或前后端同构参数来源）

## 重点检查

- 装饰器参数绑定默认不净化：`@Body()`/`@Query()`/`@Param()` 直接绑定对象/字段进业务逻辑或 sink，无显式校验
- ValidationPipe 未启用或未配置 `whitelist: true`：多余字段透传（mass assignment）、DTO 校验缺失
- Guard → Interceptor → Pipe → Handler → Interceptor → Filter 执行顺序与短路：Guard 在 Pipe 之前执行（校验可通过但鉴权在后的路由级组合），全局/路由级 Guard 的覆盖空隙
- 全局 Guard/全局前缀配置：`app.useGlobalGuards`/`setGlobalPrefix` 与控制器级 `@UseGuards` 的相互作用（全局 Guard 缺失 → 覆盖面依赖逐控制器挂载）
- 异常 Filter 默认行为：未自定义 `ExceptionFilter` 时默认响应输出堆栈/内部路径（联调 `EVID_NODE_CFG_ERR_HANDLER`）
- `@UploadedFile()` 上传链：`FileInterceptor`/`FileFieldsInterceptor` 配置与落盘路径（联调 node-file-upload-audit）
- 模块注入边界：`forRoot`/`forFeature` 动态模块、`@Global()` 模块、provider 覆盖（`useValue`/`useFactory`）导致的鉴权/校验注入替换

## 枚举规则（强制细化）

### 1. 框架边界层

- 枚举入口定义方式：`@Controller()` 控制器与 `@Get`/`@Post`/`@Put`/`@Delete`/`@All` 方法装饰器、`@Header`/`@Redirect` 响应装饰器、动态路由（`:param` 通配、`*splat` 通配）
- 枚举参数绑定点：`@Body()`/`@Query()`/`@Param()`/`@Headers()`/`@Req()` 的字段提取与直通业务逻辑/sink 的路径
- 识别请求生命周期边界：request → Middleware → Guard → Interceptor(pre) → Pipe → Handler → Interceptor(post) → ExceptionFilter → response，标注每级短路条件
- 识别模块注入边界：`@Module` 的 imports/controllers/providers、`forRoot`/`forFeature` 动态注册、`@Global()` 模块与 provider 覆盖（`useClass`/`useValue`/`useFactory`）

### 2. 运行时配置层

- 枚举 ValidationPipe 配置：`app.useGlobalPipes(new ValidationPipe(...))` 的 `whitelist`/`forbidNonWhitelisted`/`transform` 选项、DTO class-validator 装饰器（`@IsString`/`@IsInt` 等）覆盖
- 枚举全局配置：`app.setGlobalPrefix`、`app.enableCors`（通配 + `credentials` 组合）、`app.useGlobalGuards`/`app.useGlobalInterceptors`/`app.useGlobalFilters` 与路由级装饰器的叠加
- 枚举异常处理配置：`@Catch()`/`AllExceptionsFilter`/`HttpExceptionFilter` 是否自定义、默认响应是否含堆栈与内部路径（`EVID_NODE_CFG_ERR_HANDLER`）
- 枚举环境变量读取点：`ConfigModule`/`@nestjs/config` 的 `isGlobal`/`validationSchema`、`process.env` 直读、`.env` 文件敏感项
- 枚举上传配置：`FileInterceptor`/`FileFieldsInterceptor`/`AnyFilesInterceptor` 的 `limits`/`fileFilter`/`dest` 与 `@UploadedFile()` 落盘路径（联调 node-file-upload-audit）

### 3. 前置控制面层

- 枚举 Guard 覆盖范围：`@UseGuards(AuthGuard)` 是全局 `useGlobalGuards` 还是逐控制器/逐方法挂载、`@Public()`/`@SkipAuth()` 豁免装饰器、动态注册路由的 Guard 覆盖
- 识别 Guard 短路条件：Guard `canActivate` 返回值/异常抛出的 fail-close 分支、反射元数据（`@Roles` 等）读取失败时的默认行为
- 枚举 Interceptor 与 Filter：`@UseInterceptors`（日志/限流/转换）与 `@UseFilters` 的执行时机、Interceptor 内吞异常或透传原始错误的处理
- 枚举速率限制与请求大小限制：`@nestjs/throttler` 配置、body 大小限制、上传文件大小限制

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| ValidationPipe | `app.useGlobalPipes(new ValidationPipe({ whitelist: true, forbidNonWhitelisted: true }))` | 检查全局 Pipe 是否注册、`whitelist` 是否开启、DTO 类是否带 class-validator 装饰器 | `whitelist` 开启且 DTO 覆盖 → ✅ 安全；未注册 Pipe 或 `whitelist` 缺失 → 🔴 多余字段透传高危 |
| Guard 覆盖 | `app.useGlobalGuards(AuthGuard)` 或逐控制器 `@UseGuards` | 比对路由/控制器清单与 Guard 覆盖范围，含动态注册模块与 `@Public` 豁免面 | 全局或逐路由 fail-close → ✅ 安全；存在可达的无 Guard 路由 → 🔴 高危 |
| 管线顺序 | Guard 先于 Pipe 执行的默认管线 | 检查 Guard 与 ValidationPipe 的注册层级，确认鉴权是否在参数绑定/校验之前短路 | 鉴权先于业务执行且无条件放行 → ✅ 安全；校验先行导致鉴权后置可被绕过 → ⚠️ 待确认 |
| 异常 Filter | `@Catch()` 自定义 `AllExceptionsFilter` | 检查是否注册自定义全局 Filter 及响应内容是否含堆栈/内部路径 | 自定义 Filter 且响应净化 → ✅ 安全；缺失或透传默认错误 → 🔴 默认堆栈泄露（fail-open） |

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

- `EVID_NODE_CFG_SECURITY_SWITCH` 显示 ValidationPipe 未注册或 `whitelist` 缺失，`@Body()` 直绑对象进入业务/sink 且多余字段被消费（mass assignment）
- `EVID_NODE_CFG_MIDDLEWARE_ORDER` 显示 Guard 仅部分控制器挂载（`@UseGuards` 逐路由而非全局）或存在可达的无 Guard 路由，且 `@Public` 豁免面过宽
- `EVID_NODE_CFG_ERR_HANDLER` 显示未自定义 ExceptionFilter，默认错误响应含堆栈/内部路径（fail-open）
- `EVID_NODE_CFG_RUNTIME_SETTING` 显示全局配置（`setGlobalPrefix`/`useGlobalGuards`/`enableCors`）缺失或 CORS 通配 + `credentials` 组合且存在携带 Cookie 的受保护接口
- `@UploadedFile()` 上传链缺少 `fileFilter`/`limits` 且落盘路径含用户输入 → 联调 node-file-upload-audit 确认（`EVID_NODE_UPLOAD_MIDDLEWARE_CONFIG`）

### ⚠️待验证

- Guard 与 Pipe 的叠加行为（校验先行导致鉴权后置）依赖框架版本与装饰器组合，静态无法确认全部短路路径（`EVID_NODE_CFG_MIDDLEWARE_ORDER`）
- 动态模块（`forRoot`/`forFeature`）中 provider 覆盖（`useValue`/`useFactory`）导致鉴权/校验替换，需展开真实注入链确认
- class-validator 校验缺失是否可利用取决于 DTO 实际消费字段，需 trace 到 sink 确认
- 默认错误响应是否泄露堆栈取决于运行时 `NODE_ENV` 与框架版本行为，静态无法确认部署环境
- AuthGuard/JWT 策略配置（`jwt.verify` 算法/密钥来源、cookie 标志）依赖版本与部署行为，静态无法确认全部校验面（`EVID_NODE_SESS_JWT_SIGN_VERIFY_CONFIG`/`EVID_NODE_SESS_COOKIE_FLAGS`）

### 误报

- ValidationPipe 全局注册且 `whitelist: true` + `forbidNonWhitelisted: true`，DTO 类校验装饰器覆盖全部消费字段
- Guard 全局 `useGlobalGuards` 于所有控制器之前且 fail-close（未鉴权直接拒绝），`@Public` 豁免面最小化
- 自定义 ExceptionFilter 已注册且响应内容已净化（无堆栈/内部路径）
- `@UploadedFile()` 链配置了 `fileFilter` 白名单与大小 `limits`，落盘路径固定

## 测试建议（强制）

### 正向测试

- 向带 ValidationPipe 的路由发送含多余字段的 body → 应被剥离/拒绝（whitelist/forbidNonWhitelisted 生效）
- 无鉴权直接请求未挂 Guard 的控制器路由 → 应被拒绝（401/403），验证 Guard 覆盖
- 触发异常请求 → 响应应为净化错误，不包含堆栈/内部路径
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 合法请求携带有效 token 通过 Guard/Pipe 正常进入 handler
- 合法 body 通过 DTO 校验正常消费，无误拒
- 生产模式（`NODE_ENV=production`）下异常响应不泄露堆栈

### 回归测试

- 新增控制器/方法必须纳入 Guard 覆盖清单后复测
- ValidationPipe 配置变更后重验多余字段透传与 DTO 校验
- 全局配置（前缀/Guard/CORS）改动后重验覆盖范围与跨域面

## 证据引用

- `EVID_NODE_CFG_MIDDLEWARE_ORDER`（Guard/Interceptor/Pipe 执行顺序与短路条件证据）
- `EVID_NODE_CFG_SECURITY_SWITCH`（ValidationPipe whitelist、CORS、全局配置开关证据）
- `EVID_NODE_CFG_ERR_HANDLER`（异常 Filter 与堆栈泄露证据）
- `EVID_NODE_CFG_RUNTIME_SETTING`（ConfigModule/环境变量可见面证据）
- `EVID_NODE_UPLOAD_MIDDLEWARE_CONFIG`（`@UploadedFile()` 上传链配置面，联调 node-file-upload-audit）
- `EVID_NODE_SESS_JWT_SIGN_VERIFY_CONFIG` 与 `EVID_NODE_SESS_COOKIE_FLAGS`（AuthGuard/JWT 策略配置面，联调 node-auth-audit/node-session-cookie-audit）

## 输出

- `node/framework_audit/nestjs_{timestamp}.md`
- 必须写明：入口类型与挂载方式（装饰器路由/控制器）、参数绑定点与净化状态、Guard/Interceptor/Pipe/Filter 管线顺序与短路条件、ValidationPipe 配置、全局 vs 路由级守卫覆盖、异常 Filter 行为、上传链配置、模块注入边界
- 必须写明环境差异：`NODE_ENV` 分支、全局配置与开发/生产差异、框架版本行为差异
- 消费关系：影响漏洞强结论时必须显式写明如何被 `node/route_tracer`、各 `node-vuln-audit` 专项（nosql/cmd/upload/xss 等）与 `node-audit-pipeline` 消费
