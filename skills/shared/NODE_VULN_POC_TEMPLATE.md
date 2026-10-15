# Node.js 漏洞 PoC 输出模板

本文件用于统一 `node/vuln_poc` 目录下各漏洞专项的 PoC 产物格式，使其能够被 node-audit-pipeline、人工复核和 exploit-chain 聚合稳定消费。

## 适用范围

- 适用于已完成 `node/vuln_audit` 且具备可复现条件的漏洞专项
- 适用于 SQL、NoSQL、CMD、SSRF、XSS、文件上传、开放重定向、XXE、反序列化、表达式执行、SSTI、XPath、LDAP 等可以构造请求或触发链路的场景
- 不适用于完全无法构造触发条件、仅能输出框架级风险提示的场景；这类情况应在 PoC 文件中明确标注为“待验证”或“环境依赖”而不是省略

## 使用规则

- 默认输出文件为 `node/vuln_poc/{type}_{timestamp}.md`
- 每个 vuln_poc 文件必须与对应的 `node/vuln_audit/{type}_{timestamp}.md` 建立引用关系
- 每个 PoC 条目必须写明关联的 route_id、漏洞编号、触发前提、请求模板和预期结果
- 当不满足直接复现条件时，也必须输出“待验证 PoC”或“环境依赖 PoC”，不能因为无法完全复现而不生成 `node/vuln_poc` 目录
- 请求模板中的真实路由、参数、Header、Cookie、Body、文件名应尽可能来自 `node/route_mapping` / `node/route_tracer` 产物，不应凭空捏造
- 路径命名注：物理路径为下划线（`node/route_mapping/`、`node/route_tracer/`）；正文中 skill 名用连字符（route-mapper、route-tracer）
- 请求模板中禁止保留未替换的 `${var}`、`{{...}}` 模板语法；允许保留的会话占位符为 `{host}`、`{cookie}`、`{token}`、`{apiKey}`、`{jwt}`（与 `shared/IO_PATH_CONVENTION.md` 占位符清单一致）
- 所有占位符必须在“环境依赖 / 触发前提”中说明来源或替换方式

## 模板

````md
# {project_name} - {type} PoC
生成时间: {timestamp}
关联漏洞报告: node/vuln_audit/{type}_{timestamp}.md

## PoC 列表

### POC-001 - {finding_id}
- route_id: {route_id}
- 漏洞编号: {finding_id}
- 风险等级: {severity}
- 可利用性: 已确认（动态验证） / 已确认（静态证据） / 待验证 / 环境依赖
- 触发前提:
  - {condition_1}
  - {condition_2}
- 关联证据:
  - {route_tracer_evidence}
  - {framework_audit_evidence}
  - {vuln_audit_evidence}

### 请求模板

```http
POST /example HTTP/1.1
Host: {host}
Cookie: {cookie}
Authorization: Bearer {token}
Content-Type: application/json

{"key":"value"}
```

### 预期结果

- {expected_behavior}

### 动态复核记录（标注"已确认（动态验证）"时必填）

- 验证方式: {直接请求 / 最小复现工程}
- 环境: {运行环境或测试工程说明}
- 观察到的效果: {observed_behavior}
- 输出证据摘要: {response_excerpt_or_console_output}

### 验证说明

- {notes}

### 排除链

| 参数 | 进入位置 | 不成立原因 | 证据 |
| ---- | ---- | ---- | ---- |
| param_a | sink 参数位 | 被转义 / 白名单 / 整数收敛 | 具体实现位置或函数名 |
| param_b | sink 参数位 | ... | ... |
| param_c | sink 参数位 | ⚠️未验证 | 明确标注 |
````

## 可利用性状态语义

- `已确认（动态验证）`：PoC 已在运行环境 / 测试工程中**实际触发**，并观察到预期效果（有动态复核记录支撑）
- `已确认（静态证据）`：证据链闭合（入口 → 传播 → sink 均有实证），但**未实际触发**
- `待验证`：存在未闭合的证据缺口，无法给出确定结论
- `环境依赖`：复现依赖特定部署、配置或外部条件，当前环境无法满足

**措辞约束**：未完成动态复核的 PoC **禁止**标注 `已确认（动态验证）`，只能标注 `已确认（静态证据）` 或更弱状态；下游报告引用“已确认”时必须区分两种已确认，不得混用。

## 占位符规则

- `{host}`：目标主机名或基地址，来自 route-mapping 产物或用户输入
- `{cookie}`：会话 Cookie，来自已登录会话或测试账号
- `{token}`：Bearer 令牌，来自认证接口返回或测试账号
- `{apiKey}`：固定 API 密钥，来自配置/环境变量或接口返回
- `{jwt}`：JWT 令牌，来自认证接口返回或测试账号
- **禁止**保留 `${var}`、`{{...}}`、`<% %>` 等未替换模板语法
- 所有真实路由、参数名、方法必须替换为 route-mapper / route-tracer 产物中的实际值

## 动态复核（C/H 级强制）

静态证据链闭合后，C/H 级结论必须完成动态复核（以下两条路径之一），并落盘「动态复核记录」字段：

1. **启动应用直接打 PoC 请求**：在本地 / 测试环境启动目标应用，按请求模板发送真实请求，观察响应、日志或副作用（如数据库变化、文件落盘）。
2. **最小复现工程**：编写最小 Jest / Mocha / Node 脚本，直接调用目标代码路径（middleware → handler → service → sink），断言漏洞行为发生。适用于应用无法整体启动或入口难以构造的场景。

动态复核失败或被环境阻断时：必须落盘 `dynamic_verify_blocked_reason`（环境不可用/时间限制/工具缺失等），且该 PoC 结论封顶 `已确认（静态证据）`，禁止标注 `已确认（动态验证）`；L/M 级结论维持「可选但优先」，不受本强制约束。

动态复核必须记录以下字段（见模板“动态复核记录”节）：

- 验证方式（直接请求 / 最小复现工程）
- 环境（运行环境 / 测试工程说明，含依赖与配置差异）
- 观察到的效果（实际行为与预期是否一致）
- 输出证据摘要（关键响应片段 / 控制台输出 / 日志摘录，供复核者回溯）

## 排除链（为什么其他参数不成立）

对每个 sink，除了说明危险参数为什么危险，还必须说明其他参数为什么不危险。

### 规则

如果 sink 中有多个动态参数，但只有部分危险，必须**显式排除其他参数**。

不能只说“存在 SQL 注入”，必须说“`column_key` 可注入，其他参数已排除”。

### 排除链验收标准

- [ ] 如果 sink 中有 N 个动态参数，排除链必须覆盖全部 N 个参数（或明确标注“未分析”）
- [ ] 每个排除项必须有具体证据（不是“已处理”）
- [ ] 排除证据必须指向实际实现（函数源码 / 调用位置 / 白名单内容）
- [ ] 如果某个参数未分析，必须标注 `⚠️未验证` 而不是假装排除

## 最低验收要求

- 每个 PoC 条目都能对应到 `node/vuln_audit` 中的具体漏洞编号或发现编号
- 每个 PoC 条目都能对应到 route_id 或明确的非 HTTP 入口标识
- 每个 PoC 条目都要写明 已确认（动态验证） / 已确认（静态证据） / 待验证 / 环境依赖
- 标注 `已确认（动态验证）` 的条目必须附完整的动态复核记录
- 请求模板与 `node/route_mapping` / `node/route_tracer` 产物在入口、方法、参数名上保持一致
- 不允许只写“可自行构造请求”而不给出最小请求模板
- 请求模板中不得出现未替换的 `${var}` / `{{...}}` 占位
- 每个 sink 的排除链必须覆盖全部动态参数或明确标注未验证
- 输出路径符合 shared/IO_PATH_CONVENTION.md，且明确写为 `node/vuln_poc/{type}_{timestamp}.md`
