---
name: node-xxe-audit
description: Node.js XXE 审计工具。识别 libxmljs parseXml(noent:true)、xmldom/sax 的 DOCTYPE 处理开关与 xml2js/fast-xml-parser 实体配置风险，输出分级、PoC 与修复建议。
---

# Node.js XXE 审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与 XML 解析器选型、DTD / 实体开关、输入面、结果回显相关的共享抓手
- 若项目存在 XmlParser、SoapAdapter、SsoMetadataLoader、ConfigImporter 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐 XML / SOAP 入口、参数来源与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（用于确认中间件覆盖顺序与短路条件）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于补充匿名入口、P0/P1 分桶、鉴权边界或业务前置条件）
- 可选：`node/framework_audit/*_{timestamp}.md`（用于补充宿主、框架控制面、序列化配置、静态目录或运行时边界）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于跨端参数来源、字段映射与上下游联动分析）
- 本专项属于 **trace-gate**：优先消费 `node/route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline`（Node.js 扩展模式）执行，当前专项引用的 `route_id` 应与 `node/cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- libxmljs：`libxml.parseXml(xml, { noent: true })` 与 `replaceEntities: true` —— 开启后实体被替换，外部实体可达文件读取与 SSRF
- @xmldom/xmldom：`DOMParser` 对 DOCTYPE / ENTITY 声明的处理面与 `onError` 配置
- sax：`ondoctype` 事件与实体声明是否被允许进入解析流程
- xml2js：默认基于 sax，不解析外部实体（相对安全）；需核实版本与实体相关自定义配置未被扩展
- fast-xml-parser：默认忽略外部实体（相对安全）；关注旧版本已知 CVE 与 `processEntities` 自定义行为
- SAML/SSO 元数据、SOAP 消息、配置导入、上传 docx/xlsx 内嵌 XML 等二次解析入口
- 实体展开结果是否回显到响应、错误消息或触发出网请求（Blind XXE 面）

## 枚举规则（强制细化）

- 用 rg 枚举：`require\(['"]libxmljs`、`parseXml\(`、`noent`、`replaceEntities`、`DOMParser`、`@xmldom/xmldom`、`require\(['"]sax`、`ondoctype`、`xml2js`、`fast-xml-parser`、`XMLParser\(`
- 按"库 + 危险开关"成对记录：解析库名、版本（package.json / package-lock.json）、实体 / DOCTYPE 相关选项、默认行为
- 对每个解析点记录：XML 输入来源（HTTP Body / 上传文件 / 消息队列 / 配置导入 / SSO 元数据）、DOCTYPE 是否允许、结果回显或后续使用路径
- 不得仅凭"使用 xml2js / fast-xml-parser"判定高危：默认不解析外部实体，须核实版本与自定义配置后按低风险面处理
- 若存在二次封装解析器，必须逐层展开到真实解析调用点与最终选项

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| 危险实体开关 | libxmljs `noent: true` / `replaceEntities: true` | 读取 parseXml 调用选项，确认 noent 实际值与输入可控性 | `noent:false` 或未开启 → ✅ 安全；`noent:true` 且输入可控 → 🔴 高危 |
| DOCTYPE / ENTITY 声明处理 | sax `ondoctype`、xmldom DOMParser 配置 | 检查是否拒绝或剥离 DOCTYPE / ENTITY 声明 | 声明前剥离或 fail-close 拒绝 → ✅ 安全；允许 DTD 声明进入解析 → 🔴 高危 |
| 解析器默认行为 | xml2js / fast-xml-parser 默认不解析外部实体 | 核对库版本与自定义配置，确认未开启实体解析路径 | 默认行为未被自定义扩展 → 🟠 低风险面；自定义开关开启实体处理 → 🔴 高危 |
| 输入面校验 | schema 校验 / DOCTYPE 剥离 / 白名单 | 确认 XML 输入入口是否经过校验或预处理 | fail-close 校验 → ✅ 安全；无校验直接解析 → 🔴 高危 |
| 回显与外联 | 响应回显 / 错误消息 / 出网探测 | 追踪实体展开结果是否回显或触发外部请求 | 回显 / 外联可控 → 🔴 高危放大；无回显 → 🟠 Blind XXE 待确认 |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认漏洞候选`：外部可控 XML 输入疑似进入开启实体处理的解析器
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

- `EVID_NODE_XXE_PARSE_POINT` + `EVID_NODE_XXE_EXTERNAL_ENTITY_FLAG`：外部可控 XML 进入 `noent:true` 或允许 DOCTYPE 的解析器，且无 `EVID_NODE_XXE_SAFE_PARSER_ALTERNATIVE` 防护
- libxmljs `noent:true` 且 XML 输入来自 HTTP Body / 上传文件，实体展开结果回显到响应
- 允许 DOCTYPE / ENTITY 声明且解析异常信息回显，构成 Blind XXE 通道

### ⚠️待验证

- 上下文显示可疑解析（如 libxmljs 调用），但选项实际值或外部输入来源不清晰（需补 trace 或调用链）
- 二次封装解析器选项分散，无法确认最终 noent / DOCTYPE 行为
- 异步 / 消息队列 / SSO 元数据拉取链路中的 XML 来源未闭合

### 误报

- 解析器为 xml2js / fast-xml-parser 默认配置，版本无已知实体处理绕过，且输入面有 fail-close 校验
- 所有层级均剥离 DOCTYPE / 拒绝 DTD 声明（fail-close），且解析器未开启实体替换
- XML 输入仅来自可信内部常量，无外部可控来源

## 测试建议（强制）

### 正向测试

- 构造 XXE payload：`<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>`
- 构造 Billion Laughs 实体扩展与 `http://` 外联探测（Blind XXE），验证解析行为
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 构造被 barrier 拦截的输入：DOCTYPE 被剥离、外部实体解析失败、声明被拒绝
- 验证 `noent:false` 场景下实体引用保持原样、不触发外部资源访问
- 验证 schema / 白名单校验对非法 XML 明确拒绝

### 回归测试

- 修复后复测，确认 DOCTYPE 剥离与解析器配置仍然生效
- 升级 xml2js / fast-xml-parser 版本后复测默认行为未变化
- 验证新增解析入口仍走统一安全封装

## 证据引用

- `EVID_NODE_XXE_PARSE_POINT`
- `EVID_NODE_XXE_EXTERNAL_ENTITY_FLAG`
- `EVID_NODE_XXE_SAFE_PARSER_ALTERNATIVE`

## 输出

- `node/vuln_audit/xxe_{timestamp}.md`
- `node/vuln_poc/xxe_{timestamp}.md`（已确认 / 待验证 / 环境依赖 PoC）
