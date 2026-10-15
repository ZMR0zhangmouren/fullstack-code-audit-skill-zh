---
name: dotnet-grpc-audit
description: .NET gRPC 微服务通信安全审计工具。针对 gRPC 服务框架边界、Proto 文件解析、元数据安全、流式通信与服务间认证进行白盒审计。
---

# gRPC 微服务通信安全审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与 gRPC 相关的入口定义、绑定转换、前置控制、敏感操作、安全配置抓手
- 若项目存在 gRPC 二次封装、统一拦截器、客户端工厂或服务注册包装层，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md`（如项目存在 gRPC-HTTP 映射入口，用于对齐 Proto 方法与路由映射）
- 可选：`auth_audit/auth_mapping_{timestamp}.md`（如需对齐服务间 mTLS、Token 鉴权或 CallCredentials）
- 可选：`route_tracer/{route_id}/trace_{timestamp}.md`（如需将 gRPC 控制面与具体入口、副作用链做交叉引用）
- 建议扫描：`*.proto` 文件（Proto 定义与服务契约）

## 重点检查

### gRPC 服务端入口

- Grpc.Core 绑定：`Server服?.*\.BindService` / `ServerBuilder` / `Grpc.Core.Server`
- Grpc.Net.Client 客户端：`GrpcChannel` / `CallInvoker` / `HttpMessageHandler` 配置
- Proto 生成代码：`GrpcClientBase` / `ClientBase` 继承链
- 服务注册：`AddGrpc()` / `UseGrpcWeb()` 中间件配置

### Proto 文件与服务契约

- Proto 文件路径与内容：`import`、`package`、`service`、`rpc` 定义
- Proto 生成代码中的不安全字段类型：`bytes`、`repeated`、嵌套 message
- Proto 选项安全：`deprecated`、`client_streaming`、`server_streaming` 标记
- 未加密字段：密码、Token、密钥字段是否明文暴露

### gRPC 元数据（Metadata）安全

- `Metadata` 读取：`context.RequestHeaders` / `ServerCallContext.RequestHeaders`
- 元数据传递链：客户端 → 服务端 / 服务间转发
- 敏感 Header：`authorization`、`x-forwarded-*`、`custom-auth` 传递
- 元数据注入：`Metadata.Add()` 可控点
- gRPC-Web 场景：`Grpc-Web-Authorization` header 处理

### 流式 RPC 安全

- 服务端流式：`stream` 类型参数与响应处理
- 客户端流式：请求聚合与边界控制
- 双向流：`IAsyncStreamReader<T>` / `IServerStreamWriter<T>` 使用
- 流控：`WriteOptions` / `WriteOptions.Flags` 配置
- 流式拒绝服务：流数量限制、超时配置

### 服务间认证（CallCredentials）

- `CallCredentials` 配置：`CallCredentials.FromInterceptor` / `CallCredentials.FromMetadataProvider`
- Token 传递：`Authorization` header 构建与刷新
- mTLS 配置：`SslCredentials` / `GrpcChannelOptions` 的 TLS 设置
- 跨服务委托：`CallCredentials.Interceptorception` 链
- 凭证泄露：凭证是否写入日志、暴露于追踪

### gRPC-Web 安全

- gRPC-Web 中间件：`UseGrpcWeb()` 配置与 CORS 集成
- 代理转发：`grpc-web-text` 编码处理
- HTTP/1.1 降级：与 HTTP/2 gRPC 的安全差异
- 预检请求：`OPTIONS` 方法与跨域配置

### Proto 代码生成风险

- 不安全的 Proto 生成：`google/protobuf/any.proto` 使用
- 动态类型反序列化：`google.protobuf.Any` 类型解析
- Proto 与 DTO 映射：自动映射工具的注入风险
- 版本兼容性：Proto 变更与向后兼容

## 枚举规则（强制细化）

### gRPC 入口检测

搜索以下关键字并记录：

```
Grpc.Core.Server
Grpc.Core.BindService
ServerBuilder.AddService
Grpc.Net.Client.GrpcChannel
Grpc.Net.Client.CallInvoker
HttpRequestHandler (gRPC-Web)
AddGrpc()
UseGrpcWeb()
```

### Proto 文件扫描

扫描 `*.proto` 文件并记录：

```
service {service_name} {{
  rpc {method_name}({input_type}) returns ({output_type});
}}
// 标记不安全字段
// 标记 streaming 方法
```

### Metadata 安全检查

搜索以下模式：

```
Metadata.FromIncomingHeaders()
context.RequestHeaders
ServerCallContext.RequestHeaders
Metadata.Add(
GrpcWeb-Authorization
authorization
x-forwarded
```

### 认证与凭证检查

搜索以下模式：

```
CallCredentials
SslCredentials
GrpcChannelOptions
ChannelCredentials
MetadataCredentials
UseEncryption
InsecureServerOption
```

### 流式方法识别

搜索以下模式并记录流类型：

```
IAsyncStreamReader
IServerStreamWriter
IStreamObserver
stream rpc
ClientStreamingMethod
ServerStreamingMethod
BidiStreamingMethod
```

### gRPC-Web 配置检查

搜索以下模式：

```
UseGrpcWeb()
EnableGrpcWeb()
GrpcWebOptions
CorsPolicy (for gRPC)
```

## Barrier 验证矩阵（强制）

按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 三级标准评估：

| 等级 | 检查项 | 通过标准 | 失败降级 |
|------|--------|----------|----------|
| 一级 | gRPC 服务存在且可达 | Grpc.Core.Server/GrpcChannel 存在且客户端可实际建立连接调用 | BLOCKED → 无可达 gRPC 服务，专项降为低优先级 |
| 二级 | 元数据/凭证存在安全问题 | Metadata/CallCredentials 传递链断裂、InsecureServerOption 启用、或 mTLS 配置缺失 | BLOCKED → 元数据与凭证链完整安全，结论降级 |
| 三级 | 流式/Proto 风险可导致利用 | Streaming 方法未鉴权/无限流、Proto bytes 类型导致反序列化风险、或 gRPC-Web 降级引入跨域问题 | PARTIAL → 仅输出潜在风险与验证步骤 |

## 二阶段判定流程（强制）

- **阶段 1（初筛命中）**：命中 gRPC 服务绑定 + 元数据/凭证配置 + 流式/Proto 风险，输出 `命中ID：M{hash}`。
- **阶段 2（精筛确认）**：
  1. 逆向追踪 Proto service/rpc → gRPC 服务绑定 → 拦截器/凭证 链路；
  2. 验证 Metadata/CallCredentials/SslCredentials 传递链与 InsecureServerOption 配置；
  3. 评估 Streaming 方法鉴权/限流、Proto bytes 反序列化、gRPC-Web CORS 降级风险；
  4. 若三级 Barrier 全部通过 → `确认漏洞`；任一失败 → 按矩阵降级。

## 判定规则与优先级（强制）

1. **确认漏洞**：gRPC 服务可达 + 元数据/凭证不安全 + 流式/Proto 风险可利用。输出 `确认漏洞`。
2. **待确认**：gRPC/元数据/流式证据部分存在，但拦截器顺序或 scale-out 行为不可证实。输出 `待确认`。
3. **误报/无风险**：gRPC 服务不可达或已保护，mTLS/CallCredentials 完整，Streaming 有鉴权与限流，Proto 定义安全。输出 `误报` 并给出判定依据。

## 测试建议与最小触发条件（强制）

- **最小触发条件**：
  - 存在 gRPC 服务（Grpc.Core/Grpc.Net.Client）
  - 客户端可建立连接并调用 rpc 方法
  - 或 Metadata/CallCredentials 传递链断裂、InsecureServerOption 启用
  - 或 Streaming 方法未鉴权、Proto bytes 类型不安全
- **测试用例建议**：
  - Happy Path：正常 gRPC 请求经 mTLS 与 CallCredentials 处理，返回正确响应
  - 边界/歧义：Metadata 头注入、InsecureServerOption 明文传输、Streaming 无限流 DoS、Proto Any 类型反序列化、gRPC-Web CORS 绕过
- 每条命中输出追加 `命中ID：M{hash}` 和 `test_id：T{hash}`，用于回溯。

## 证据引用
```

## 证据引用

- EVID_GRPC_SERVER_BIND：gRPC 服务绑定入口证据
- EVID_GRPC_METADATA_SOURCE：Metadata 来源与传递链证据
- EVID_GRPC_STREAM_HANDLER：流式处理入口证据
- EVID_GRPC_CREDS_CONFIG：CallCredentials / TLS 配置证据
- EVID_GRPC_PROTO_DEFINITION：Proto 定义与服务契约证据
- EVID_GRPC_WEB_ENDPOINT：gRPC-Web 端点暴露证据
- EVID_AUTH_PATH_PROTECTED_MATCH：受保护入口匹配证据（跨专项）
- EVID_SESS_JWT_VERIFY_CLAIMS：JWT 校验证据（跨专项）

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（服务入口确认）**：必须确认 gRPC 服务绑定点与 Proto 方法映射。
- 🔴 **CHECKPOINT B（元数据与凭证确认）**：必须确认 Metadata/CallCredentials 传递链。
- 🔴 **CHECKPOINT C（流式边界确认）**：必须确认 streaming 方法的鉴权与限流边界。
- 🛑 **STOP**：若服务契约与认证链未闭合，结论降级为 `⚠️待验证/环境依赖`。

## 失败场景与兜底（if-then）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| Proto 契约与服务绑定映射不完整 | 补齐 `service/rpc -> bind/register` 证据 | 降级 `⚠️待验证/环境依赖` |
| Metadata/凭证传递链断裂 | 追踪客户端到服务端关键头传播 | 暂不输出绕过确认，仅给验证路径 |
| streaming 鉴权与限流证据不足 | 补齐流式方法权限与配额配置 | 保守评估风险，不做强结论 |

🔴 **STOP：任一兜底触发时，禁止输出“认证可绕过”强结论。**

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

- 反模式：只看 Proto 定义不看运行时拦截链。正确做法：结合服务绑定、拦截器与凭证配置审计。
- 反模式：忽略 Metadata 透传污染。正确做法：追踪关键头从客户端到服务端链路。
- 反模式：把 gRPC-Web 与 gRPC 原生安全等同。正确做法：区分 HTTP/1.1 降级与跨域边界。
- 反模式：证据不足仍判认证可绕过。正确做法：降级 `⚠️待验证/环境依赖`。

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

- framework_audit/grpc_{timestamp}.md
- 必须写明服务入口类型、Proto 契约映射、Metadata 安全面、流式通信风险、认证配置、与认证/会话专项的联动关系
- 如发现凭证泄露或认证绕过，额外输出 `vuln_poc/grpc_{timestamp}.md`

## 与其他专项的联动

- 本 Skill 产生的 `route_id` 或 `service_id` 可传递给 `dotnet-auth-audit` 用于服务间认证检查
- `Metadata` 中的 Token 可传递给 `dotnet-session-cookie-audit` 用于会话校验
- Proto 定义中的 `bytes` 类型可能涉及 `dotnet-deser-audit` 相关风险