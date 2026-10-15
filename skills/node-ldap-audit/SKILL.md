---
name: node-ldap-audit
description: Node.js LDAP 注入审计工具。识别 ldapjs search({filter}) / bind 的 filter 与 DN 拼接、RFC 4515 转义缺失与匿名绑定回退风险，输出可利用性分级、PoC 与修复建议。
---

# Node.js LDAP 注入审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与 LDAP filter 构造、DN 拼接、绑定方式、搜索边界、认证旁路相关的共享抓手
- 若项目存在 LdapService、AuthAdapter、DirectoryConnector、SyncConnector 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐登录 / 目录查询入口、参数来源与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（用于确认中间件覆盖顺序与短路条件）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于补充匿名入口、P0/P1 分桶、鉴权边界或业务前置条件）
- 可选：`node/framework_audit/*_{timestamp}.md`（用于补充认证集成、宿主配置与运行时控制面）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于跨端参数来源、字段映射与上下游联动分析）
- 本专项属于 **trace-gate**：优先消费 `node/route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline`（Node.js 扩展模式）执行，当前专项引用的 `route_id` 应与 `node/cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- ldapjs `client.search(base, { filter: ... })`：filter 字符串拼接用户输入且未转义 LDAP 元字符
- `client.bind(dn, password)`：认证绑定 DN / 凭据拼接导致的认证绕过
- DN 构造：`cn=${user},ou=people,dc=...` 等 RDN 组件拼接的 RFC 4514 转义
- RFC 4515 元字符（`*`、`(`、`)`、`\`、NUL）转义实现与拼接顺序
- bind 失败后的匿名绑定 / 继续放行 fallback 行为
- scope、attributes、base 参数用户可控导致的越权查询
- 登录验证、用户搜索、组成员查询、目录同步、SSO 断言内容进入 filter 的路径

## 枚举规则（强制细化）

- 用 rg 枚举：`require\(['"]ldapjs`、`createClient\(`、`\.search\(`、`\.bind\(`、`escapeFilter`、`scope`、`attributes`、`baseDN|baseDn|searchBase`
- 枚举登录、用户搜索、组成员查询、同步任务、SSO 集成中的 filter 与 DN 构造位置
- 对每个调用点记录：filter / DN 构造方式、转义实现、绑定方式、scope / attributes 来源、结果参与认证与授权的路径
- 区分认证绑定（bind）与搜索查询（search）两类风险语义，bind 场景单独标注
- 若存在二次封装，必须逐层展开到真实 `client.search` / `client.bind` 调用点

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| Filter 字符串拼接 | `search(base, { filter: 'uid=' + user })` | 读取 filter 构造源码，确认是否来自字符串拼接 / 模板插值 | 用户输入参与拼接且无 RFC 4515 转义 → 🔴 高危；固定模板 + 转义值位 → 🟠 需确认值位边界 |
| RFC 4515 转义实现 | 自封装 `escapeFilter()` | 读取实现源码，确认 `*` `(` `)` `\` NUL 与控制字符处理、是否在拼接前完成 | 完整转义且 fail-close → ✅ 安全；部分转义 → ⚠️ 可绕过；无转义 → 🔴 高危 |
| DN 构造（RFC 4514） | `cn=${user},ou=people` 拼接 | 确认 DN 组件转义实现与来源 | RFC 4514 转义 → ✅ 安全；无转义 → 🔴 高危 |
| 认证绑定语义 | `client.bind(dn, password)` | 区分 bind 与 search，确认 bind DN / 凭据是否用户可控 | bind DN 拼接可控 → 🔴 认证绕过；固定服务账号 → ✅ 安全 |
| 匿名绑定 fallback | bind 失败 catch 中回退匿名或继续放行 | 读取错误处理分支与后续放行逻辑 | bind 失败即拒绝（fail-close）→ ✅ 安全；回退匿名 / 继续放行 → 🔴 高危 |
| 搜索范围与属性 | scope / attributes / base 参数 | 确认 scope、attributes、base 是否来自用户输入 | 固定范围 + 属性白名单 → ✅ 安全；用户可控 → 🟠 需确认影响面 |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认漏洞候选`：外部可控输入疑似进入 filter / DN 拼接或认证绑定凭据位
- `待确认`：上下文显示可疑模式，但外部输入来源、barrier 行为或调用链不清晰
- `误报`：输入来自固定常量 / 枚举映射，或 barrier 已验证为 fail-close

### 阶段二：强制追证

若阶段一为「待确认」，必须继续向下追至少一跳调用链或下游解析器，直到满足以下任一条件：

- 找到外部可控输入进入 Sink 位的证据 → `确认漏洞`
- 找到固定白名单映射 / fail-close 证据 → `误报`
- 仍缺少关键调用链 → 保持 `待确认`，但必须说明缺失哪一跳

**fail-close 语义**：对 barrier、白名单、校验器、过滤器必须以失败模式评估。未知 / 非法输入必须抛异常、返回空、拒绝执行或日志告警，绝不能透传原始值；任何 silent-fallback 或 fail-open 行为均视为高危。

## 判定规则（强制细化）

### 已确认

- `EVID_NODE_LDAP_SEARCH_POINT` + `EVID_NODE_LDAP_FILTER_CONCAT` + 无有效 `EVID_NODE_LDAP_ESCAPE_IMPLEMENTATION`
- `EVID_NODE_LDAP_BIND_ANONYMOUS_FALLBACK`：bind 失败后回退匿名绑定并放行后续鉴权逻辑
- 认证绑定场景 DN / filter 拼接用户名，可注入 `*)(` 闭合 filter 实现认证绕过
- filter 拼接处转义实现 fail-open 或可双重编码绕过

### ⚠️待验证

- 上下文显示可疑模式（如 `client.search` 调用），但外部输入来源不清晰（需补 trace 或调用链）
- 转义函数存在，但当前分支是否调用、返回值是否被使用无法确认
- 异步 / 队列 / 事件链路（如目录同步任务、SSO 断言）中的参数传递未闭合

### 误报

- filter / DN 来自固定常量 / 枚举映射，未知输入会拒绝执行（fail-close）
- 所有层级均复用同一 RFC 4515/4514 转义函数，且转义在拼接前完成
- bind 使用固定服务账号凭据，用户输入仅进入已严格转义的值位

## 测试建议（强制）

### 正向测试

- 构造 LDAP 注入 payload：`*)(uid=*))(&(uid=*`、`admin*)(objectClass=*`、`cn=admin\00`
- 验证 bind 场景注入实现认证绕过、search 场景注入扩大查询范围
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 构造被 barrier 拦截的输入：未转义元字符被正确转义、非法 DN 格式被拒绝
- 验证 bind 失败时明确拒绝、不回退匿名绑定
- 验证转义函数对双重编码输入的处理结果

### 回归测试

- 修复后复测，确认转义与拒绝逻辑仍然生效
- 升级 ldapjs 版本后复测 filter 解析行为未变化
- 验证新增 LDAP 查询入口仍走统一转义封装

## 证据引用

- `EVID_NODE_LDAP_SEARCH_POINT`
- `EVID_NODE_LDAP_FILTER_CONCAT`
- `EVID_NODE_LDAP_ESCAPE_IMPLEMENTATION`
- `EVID_NODE_LDAP_BIND_ANONYMOUS_FALLBACK`

## 输出

- `node/vuln_audit/ldap_{timestamp}.md`
- `node/vuln_poc/ldap_{timestamp}.md`（已确认 / 待验证 / 环境依赖 PoC）
