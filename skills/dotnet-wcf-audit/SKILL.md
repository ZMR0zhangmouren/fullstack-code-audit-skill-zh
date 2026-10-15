---
name: dotnet-wcf-audit
description: WCF 框架专项审计工具。针对 SOAP/WCF 服务的绑定、安全模式、序列化、消息检查器与服务契约暴露进行白盒审计。
---

# WCF 框架专项审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与 wcf 相关的入口定义、绑定转换、前置控制、敏感操作、安全配置抓手
- 若项目存在框架二次封装、统一扩展方法、平台基座或宿主包装层，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（如已由 `dotnet-route-mapper` 生成，用于对齐服务操作、消息参数与 `route_id`）
- 可选：`auth_audit/auth_mapping_{timestamp}.md`（如需对齐服务契约授权、匿名操作与资源归属边界）
- 可选：`route_tracer/{route_id}/trace_{timestamp}.md` 与 `route_tracer/{route_id}/trace_summary_{timestamp}.md`（如需将消息处理器、序列化链与具体副作用路径做交叉引用）

## 重点检查

- BasicHttpBinding、WSHttpBinding、NetTcpBinding、NetNamedPipeBinding、安全模式、传输保护和消息级保护配置
- NetDataContractSerializer、DataContractSerializer、XmlSerializer、XmlReader、XDocument、MessageContract、KnownTypes、BinaryMessageEncoding 和消息体解析边界
- ServiceAuthorizationManager、PrincipalPermission、自定义消息检查器、行为扩展、身份模拟与客户端证书校验
- MEX 元数据暴露、svc 调试页面、IncludeExceptionDetailInFaults、详细 fault、诊断跟踪和服务清单泄露
- SOAP Header、WS-Security、会话、可靠消息、事务、回调契约和双工通信中的状态边界
- 旧版 .NET Framework 宿主、IIS/WAS、自托管 Windows Service、端口暴露与防护策略差异

## 枚举规则（强制细化）

- 枚举所有 ServiceContract、OperationContract、Binding、BehaviorExtension、MessageInspector、ServiceAuthorizationManager、PrincipalPermission 和宿主配置项
- 优先搜索 BasicHttpBinding、WSHttpBinding、NetTcpBinding、NetNamedPipeBinding、security mode、IncludeExceptionDetailInFaults、serviceMetadata、mex、KnownType、NetDataContractSerializer、XmlReader、XDocument、DtdProcessing、XmlResolver、XmlSerializerFormat
- 枚举 SOAP Header、MessageContract、事务、可靠消息、双工回调、会话实例模式、证书验证、身份模拟，以及 XmlResolver、DtdProcessing、XslCompiledTransform 相关解析配置，记录状态保持与信任边界
- 枚举 web.config、app.config、自托管初始化代码与 IIS/WAS 宿主配置，记录调试开关、元数据暴露、绑定地址和传输保护差异
- 对每个服务操作记录：绑定方式、认证方式、序列化器、消息检查器、异常/fault 输出、宿主环境与可达性

## Barrier 验证矩阵（强制）

按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 三级标准评估：

| 等级 | 检查项 | 通过标准 | 失败降级 |
|------|--------|----------|----------|
| 一级 | 服务端点存在且可达 | ServiceContract/OperationContract 存在且宿主（IIS/WAS/自托管）暴露可访问 | BLOCKED → 无可达 WCF 端点，专项降为低优先级 |
| 二级 | 绑定/序列化存在安全问题 | BasicHttpBinding 无传输保护、NetDataContractSerializer/XmlSerializer 存在反序列化风险、XmlResolver/DtdProcessing 不安全 | BLOCKED → 绑定安全且序列化配置无风险，结论降级 |
| 三级 | 授权/元数据暴露导致可利用 | ServiceAuthorizationManager/PrincipalPermission 缺失，或 MEX/introspection/fault 详细信息生产环境暴露 | PARTIAL → 仅输出潜在风险与验证步骤 |

## 二阶段判定流程（强制）

- **阶段 1（初筛命中）**：命中 WCF 服务端点 + 绑定/序列化配置 + 授权/元数据暴露，输出 `命中ID：M{hash}`。
- **阶段 2（精筛确认）**：
  1. 逆向追踪 ServiceContract → Binding → 宿主配置 链路，确认端点可达性；
  2. 验证 BasicHttpBinding/WSHttpBinding 安全模式、NetDataContractSerializer/XmlSerializer 反序列化风险、XmlResolver/DtdProcessing 配置；
  3. 评估 ServiceAuthorizationManager/PrincipalPermission 缺失与 MEX/fault 详细信息暴露；
  4. 若三级 Barrier 全部通过 → `确认漏洞`；任一失败 → 按矩阵降级。

## 判定规则与优先级（强制）

1. **确认漏洞**：端点可达 + 绑定/序列化不安全 + 授权缺失/元数据暴露。输出 `确认漏洞`。
2. **待确认**：端点/绑定/授权证据部分存在，但宿主环境或运行时配置不可证实。输出 `待确认`。
3. **误报/无风险**：端点不可达或已保护，绑定启用传输/消息级安全，序列化配置安全，授权完整，元数据不暴露。输出 `误报` 并给出判定依据。

## 测试建议与最小触发条件（强制）

- **最小触发条件**：
  - 存在 WCF ServiceContract/OperationContract
  - 宿主（IIS/WAS/自托管）暴露且端点可达
  - 或 BasicHttpBinding 无传输保护、NetDataContractSerializer 反序列化风险
  - 或 ServiceAuthorizationManager 缺失、MEX/fault 详细信息暴露
- **测试用例建议**：
  - Happy Path：正常 SOAP 请求经安全绑定与授权处理，返回正确响应
  - 边界/歧义：NetDataContractSerializer 类型混淆、XmlResolver DTD 注入、IncludeExceptionDetailInFaults 信息泄露、身份模拟越权
- 每条命中输出追加 `命中ID：M{hash}` 和 `test_id：T{hash}`，用于回溯。

## 工作流（输入→执行→输出）

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（端点与绑定确认）**：必须确认服务端点、Binding 与消息编码配置。
- 🔴 **CHECKPOINT B（消息安全确认）**：必须确认传输/消息级安全与证书策略。
- 🔴 **CHECKPOINT C（操作链确认）**：必须确认 OperationContract 到下游敏感操作链闭合。
- 🛑 **STOP**：若端点安全与调用链未闭合，结论降级为 `⚠️待验证`。

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

## 输出要求

- 输出文件：framework_audit/wcf_{timestamp}.md
- 必须按 绑定与传输保护、消息与序列化、授权与行为扩展、元数据与宿主暴露 四个章节组织结果
- 每个问题点必须写明 服务契约、操作名、绑定类型、安全模式、消息检查器或行为扩展、运行宿主
- 必须单列 仅 .NET Framework / IIS / WAS / 自托管 才成立的环境差异，避免泛化结论

## 证据引用

- EVID_AUTH_TOKEN_DECODE_JUDGMENT
- EVID_DESER_OBJECT_TYPE_MAGIC_TRIGGER_CHAIN
- EVID_XXE_ENTITY_DOCTYPE_SAFETY_AND_ECHO
- EVID_CFG_SECURITY_SWITCH_EVIDENCE

## 失败与降级分支（强制）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| 无法定位真实宿主（IIS/WAS/自托管） | 输出已识别绑定与配置证据 | 结论降级为 `⚠️环境依赖`，禁止强结论 |
| ServiceBehavior/Binding 配置来源不完整 | 同步枚举代码配置与 config 文件 | 缺失项列入待补证并标记 PARTIAL |
| 消息检查器/授权管理器实现不可解析 | 记录接口、注册点与候选实现 | 无法收敛时保留候选集合并降级 |
| 仅发现不安全开关但无可达操作证据 | 输出配置风险与影响范围 | 不输出“已确认可利用”，仅风险提示 |

🔴 **STOP：宿主与绑定证据未闭合时，不得输出“确认可利用”或 P0 结论。**

## 资源引用与可达性校验（强制）

- 必引共享索引：`skills/shared/DOTNET_AUDIT_GRABBER_INDEX.md`（抓手来源）与 `skills/shared/EVIDENCE_POINT_IDS.md`（证据口径）。
- 输出口径校验：落盘路径与命名必须对齐 `skills/shared/IO_PATH_CONVENTION.md`，不得自定义偏离目录。
- 证据一致性校验：若引用分级结论，需与 `skills/shared/SEVERITY_RATING.md` 保持一致。
- 可达性检查：提交前至少确认一次关键引用文件可访问（例如 `DOTNET_AUDIT_GRABBER_INDEX.md`、`IO_PATH_CONVENTION.md`）。

## 实测用例与通过标准（强制）

- 每个 skill 至少维护 2 个典型测试用例（happy path + 一条复杂场景），并在结果中标注用例 ID。
- 每轮评估至少 1 条用例执行 `full_test`；若受限只能 `dry_run`，必须记录 `dry_run_reason` 与补测计划。
- 通过标准至少同时满足：`意图达成`、`关键证据命中`、`输出格式合规`；任一不满足不得给出“通过”。

## 整体架构与冗余控制（强制）

- 章节组织必须保持三层骨架：`输入约束` → `执行步骤` → `输出与验收`，不得缺层或跨层混写。
- 单段建议不超过 6 行；同义规则禁止重复出现两次以上，重复内容需合并到唯一真源章节。
- 禁止 AI 腔与空话衔接词堆叠（如“首先/其次/最后/综上/说白了/换句话说”）；发现即改为可执行语句。

## 质量门禁与评估一致性（强制）

- 产出前必须执行最小门禁自检：`输入完整性`、`关键证据命中`、`输出路径合法` 三项全部为 PASS。
- 若存在 `关键证据缺失`、`链路未闭合`、`consistency_check_status=BLOCKED` 任一条件，结论必须降级为 `BLOCKED`，禁止输出“确认可利用/可交付”。
- 报告中必须显式记录：`gate_status`、`blocked_reasons`、`recheck_action`，并与 `quality/*` 产物可回溯对齐。

## 不要做的事（反例黑名单）

| # | 反模式 | 为什么不要做 | 正确做法 |
|---|---|---|---|
| 1 | 把框架默认行为当项目真实配置 | WCF 常有环境覆写 | 必须给出项目实际配置来源 |
| 2 | 只看契约不看宿主 | 风险成立依赖暴露面 | 同时记录契约、绑定与宿主 |
| 3 | 忽略消息检查器执行顺序 | 会误判防护是否生效 | 输出行为扩展/检查器顺序证据 |

输出类型映射：AUTH、DESER、XXE、CFG、SESS。
