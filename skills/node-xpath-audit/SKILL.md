---
name: node-xpath-audit
description: Node.js XPath 注入审计工具。识别 xpath.select+xmldom 与 libxmljs find 的 XPath 表达式拼接、参数化缺失与查询结果进入鉴权决策风险，输出可利用性分级、PoC 与修复建议。
---

# Node.js XPath 注入审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与 XPath 表达式构造、XML 数据源、查询结果流向相关的共享抓手
- 若项目存在 XmlQueryHelper、XPathHelper、ConfigQuerier、DocumentNavigator 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐 XML 查询入口、参数来源与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（用于确认中间件覆盖顺序与短路条件）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于补充匿名入口、P0/P1 分桶、鉴权边界或业务前置条件）
- 可选：`node/framework_audit/*_{timestamp}.md`（用于补充 XML 解析配置、XPath 引擎与运行时控制面）
- 可选：`node/vuln_audit/xxe_{timestamp}.md`（XPath 注入与 XXE 存在交叉，可复用部分发现）
- 本专项属于 **trace-gate**：优先消费 `node/route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline`（Node.js 扩展模式）执行，当前专项引用的 `route_id` 应与 `node/cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- xpath 包 + @xmldom/xmldom：`xpath.select("//user[name='" + user + "']", doc)` 表达式拼接
- libxmljs：`doc.find("//user[@name='" + user + "']")` 与 `doc.get(...)` 表达式拼接
- Node 侧主流 XPath 库（xpath / libxmljs）无原生变量绑定 API：防御依赖白名单与转义，需显式确认替代防护
- XML 数据源：配置 XML、请求 Body、SSO/SAML 响应、消息队列消息、数据库 XML 列
- 查询结果进入鉴权、业务决策、响应回显或日志的路径
- 与 node-xxe-audit 的边界：解析器配置 / 实体处理由 XXE 专项覆盖，本专项关注 XPath 查询层

## 枚举规则（强制细化）

- 用 rg 枚举：`require\(['"]xpath`、`xpath\.select|xpath\.select1`、`\.find\(`、`\.get\(`、`@xmldom/xmldom|DOMParser`、`libxmljs|parseXml`
- 枚举表达式拼接与插值位置：rg `//`、`@`、`text\(\)`、`contains\(`，回溯命中表达式中变量来源
- 枚举 XML 数据来源：配置文件加载、HTTP 请求 Body、SSO/SAML 响应、消息队列消息、数据库 XML 列
- 对每个查询点记录：表达式构造方式、参数来源、是否白名单 / 转义、XML 来源、结果使用方式
- 若存在二次封装查询器，必须逐层展开到真实 `xpath.select` / `doc.find` 调用点

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| XPath 表达式拼接 | `xpath.select('//' + tag + '[...]', doc)` | 读取表达式构造源码，确认是否来自字符串拼接 / 模板插值 | 用户输入参与拼接 → 🔴 高危；固定表达式 + 无插值 → ✅ 安全 |
| 参数化 / 变量绑定 | Node 主流 xpath 库（xpath / libxmljs）无原生变量绑定 API | 确认是否存在参数化替代封装（fail-close 拼接器 / 预编译缓存） | 有 fail-close 封装 → ✅ 安全；无原生参数化且无替代防护 → 🔴 高危 |
| 输入白名单 | 正则 `[a-zA-Z0-9_-]` / 枚举映射 | 读取校验实现，确认覆盖引号、括号等 XPath 元字符且 fail-close | fail-close 白名单 → ✅ 安全；仅转义引号 → ⚠️ 可绕过；无校验 → 🔴 高危 |
| 查询结果敏感语义 | 结果进入鉴权 / 业务判断 | 追踪查询结果流向 | 进入鉴权决策 → 🔴 高危放大；仅内部日志 → 🟠 需确认 |
| 解析器配置联动 | XML 解析层实体配置 | 解析层风险由 node-xxe-audit 覆盖，发现交叉时移交复核 | 解析配置异常 → 移交 XXE 专项；仅查询层问题 → 本专项处理 |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认漏洞候选`：外部可控输入疑似进入 XPath 表达式拼接位
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

- `EVID_NODE_XPATH_SELECT_POINT` + `EVID_NODE_XPATH_CONCAT` + 无有效 `EVID_NODE_XPATH_PARAM_BINDING`
- 查询结果进入鉴权 / 敏感业务判断，且表达式拼接位外部可控
- 输入白名单 / 转义实现 fail-open 或可通过编码 / 双重转义绕过

### ⚠️待验证

- 上下文显示可疑模式（如 `xpath.select` 调用），但外部输入来源不清晰（需补 trace 或调用链）
- 存在参数化替代封装，但当前分支是否调用、返回值是否被使用无法确认
- 异步 / 队列 / SSO 响应链路中的 XML 来源与表达式参数传递未闭合

### 误报

- XPath 表达式来自固定常量，未知输入会拒绝执行（fail-close）
- 用户输入仅进入 fail-close 白名单校验后的值位，表达式结构完全固定
- 查询结果仅用于内部日志且不回显，无鉴权 / 业务决策影响

## 测试建议（强制）

### 正向测试

- 构造 XPath 注入 payload：`' or '1'='1`、`' or ''='`、`//user[password/text()='x' or '1'='1']`
- 验证鉴权查询场景注入实现认证绕过与数据提取
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 构造被 barrier 拦截的输入：元字符被转义 / 拒绝、白名单外标签名
- 验证 fail-close 拼接封装下非法输入返回空结果
- 验证白名单校验器对编码变体的拒绝行为

### 回归测试

- 修复后复测，确认白名单与封装仍然生效
- 升级 xpath / libxmljs / xmldom 版本后复测查询行为未变化
- 验证新增 XPath 查询入口仍走统一封装

## 证据引用

- `EVID_NODE_XPATH_SELECT_POINT`
- `EVID_NODE_XPATH_CONCAT`
- `EVID_NODE_XPATH_PARAM_BINDING`

## 输出

- `node/vuln_audit/xpath_{timestamp}.md`
- `node/vuln_poc/xpath_{timestamp}.md`（已确认 / 待验证 / 环境依赖 PoC）
