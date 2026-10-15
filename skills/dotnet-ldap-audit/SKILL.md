---
name: dotnet-ldap-audit
description: .NET LDAP 注入审计工具。识别 DirectorySearcher、PrincipalContext 和自定义 LDAP Filter / DN 字符串拼接中的注入风险。
---

# .NET LDAP 审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与 LDAP 过滤器、目录查询、绑定、搜索基准、属性映射和认证旁路相关的共享抓手
- 若项目存在 DirectoryService、AuthAdapter、PrincipalHelper、SyncConnector 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（用于对齐登录/目录查询入口、参数来源与 `route_id`）
- 可选：`framework_audit/*_{timestamp}.md`（用于补充认证集成、宿主配置与运行时控制面）
- trace-gate 场景下优先消费：`route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline` 执行，当前专项引用的 `route_id` 应与 `cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- DirectorySearcher.Filter 的字符串拼接：用户输入未转义 LDAP 元字符（*、(、)、\、NUL）
- DN（Distinguished Name）拼接：用户输入进入 CN=、OU= 等 RDN 组件
- PrincipalContext / PrincipalSearcher 的 filter 参数来源
- SearchRequest 的 filter 与 baseDN 参数可控性
- 登录验证中的 LDAP bind：用户名注入导致认证绕过
- 组织树浏览、用户搜索、组成员查询中的 filter 构造
- SSO/SAML 集成中的 LDAP 查询与属性映射

## 证据引用

- EVID_LDAP_EXEC_POINT
- EVID_LDAP_FILTER_STRING_CONSTRUCTION
- EVID_LDAP_USER_PARAM_TO_FILTER_FRAGMENT

## 枚举规则（强制细化）

- 枚举 DirectorySearcher、PrincipalSearcher、SearchRequest、SearchResponse、自定义 LDAP 客户端与认证服务
- 优先搜索 Filter、DistinguishedName、baseDn、searchRoot、PrincipalContext、group search 等关键字段
- 枚举登录、用户搜索、组织树浏览、同步任务、角色映射、SSO 集成中的 LDAP 查询与 DN 构造位置
- 对每个 LDAP 调用点记录：filter 来源、转义策略、绑定方式、搜索范围、查询结果如何参与认证和授权

## Barrier 验证矩阵（强制）

本专项必须对以下 barrier 类型执行验证，按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 标准评估：

| Barrier 类型 | 验证动作 | 判定标准 |
|-------------|---------|---------|
| **Filter 字符串拼接** | 读取 `DirectorySearcher.Filter` 或 `SearchRequest.Filter` 构造源码，确认是否来自字符串拼接/插值 | 用户输入参与 Filter 拼接且无 RFC 4515 转义 → 🔴 高危；固定 Filter 模板 + 参数化值位 → 🟠 需确认值位边界 |
| **DN（Distinguished Name）拼接** | 确认用户输入是否进入 CN=、OU=、DC= 等 RDN 组件的拼接 | 用户输入进入 DN 拼接且无 RFC 4514 转义 → 🔴 高危；固定 DN 路径 → ✅ 安全 |
| **RFC 4515/4514 转义** | 读取转义函数实现源码，确认是否处理了 LDAP 元字符（`*`、`(`、`)`、`\`、NUL） | 完整转义且 fail-close → ✅ 安全；部分转义或转义在拼接之前 → ⚠️ 可绕过；无转义 → 🔴 高危 |
| **绑定模式与认证用途** | 区分认证绑定（bind）与搜索查询（search）场景，确认 bind 场景下用户名是否可控 | 认证绑定中用户名可控 → 🔴 高危（认证绕过）；搜索查询中 Filter 可控 → 🟠 需评估影响面 |
| **搜索范围与属性白名单** | 确认 `SearchScope` 和查询属性是否来自用户输入，是否限制在预期范围内 | 用户可扩大搜索范围或读取敏感属性 → 🔴 高危；固定范围且属性白名单 fail-close → ✅ 安全 |
| **SSO/SAML 集成中的 LDAP 查询** | 确认 SSO/SAML 集成中的 LDAP 查询是否将外部断言/令牌内容直接送入 Filter | 外部断言内容直接进入 Filter → 🔴 高危；有校验层且 fail-close → ✅ 安全 |

🔴 **STOP：任一 barrier 验证为 `silent-fallback` 或 `fail-open` 时，禁止将结论标记为「已确认安全」或「误报」。**

## 二阶段判定（强制）

遵循 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

1. **阶段一（临时结论）**：对每条命中先标记 `确认漏洞候选` / `待确认` / `误报`
2. **阶段二（强制追证）**：
   - 若阶段一为 `确认漏洞候选` → 必须完成 Barrier 验证矩阵全部相关项，通过后才能标记 `已确认`
   - 若阶段一为 `待确认` → 必须向下追至少一跳调用链或下游解析器，直到可判定为止
   - 若阶段二仍无法闭合 → 保持 `待确认`，并明确记录缺失哪一跳证据

## 判定规则（强制细化）

### 确认漏洞

至少满足以下任一条件：

1. 用户可控输入直接进入 Filter/DN 字符串拼接位置，且无 RFC 4515/4514 转义
2. LDAP 元字符（`*`、`(`、`)`、`\`、NUL）未转义即进入 Filter 构造
3. 认证绑定（bind）场景中用户名来自用户可控输入，可导致认证绕过
4. 转义函数为 fail-open 或 silent-fallback，可通过编码/双重转义绕过
5. 嵌套/递归结构（如多层 DirectoryService 封装）中顶层存在校验，但子层未执行同级校验

### 待确认

1. 上下文显示可疑模式（如 `DirectorySearcher` 调用），但外部输入来源不清晰（需补 trace 或调用链）
2. Barrier 函数（如 RFC 转义函数）存在，但当前分支是否调用、返回值是否被使用无法确认
3. 异步 / 队列 / 事件链路（如后台同步任务）中的参数传递未闭合
4. SSO/SAML 集成中的 LDAP 查询链路复杂，外部断言到 Filter 的映射未完全闭合

### 误报

1. 最终 Filter/DN 来自固定常量 / 枚举映射，未知输入会拒绝执行（fail-close）
2. 递归所有层级均复用同一 RFC 转义函数，且转义函数为 fail-close
3. 用户输入仅进入已严格转义的值位，且转义在字符串拼接之前完成
4. 搜索范围、属性列表完全固定，用户无法控制查询边界

## 测试建议（强制）

遵循 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的测试要求，对每个确认漏洞或待验证项给出：

- **正向测试**：构造 LDAP 注入 payload（如 `*)(uid=*))(&(uid=*`、`admin*)(objectClass=*`、`cn=admin\00`），验证注入/认证绕过确实存在
- **负向测试**：构造被 barrier 拦截的输入（如未转义元字符被正确转义、非法 DN 格式被拒绝），验证保护机制有效
- **回归测试**：修复后复测，确认 barrier 仍然生效，且未引入新的绕过路径

测试用例应标注 `test_id`，并在审计报告中与对应命中 ID 关联。


## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（查询点确认）**：必须确认 LDAP 执行点与绑定方式。
- 🔴 **CHECKPOINT B（过滤器映射确认）**：必须给出输入到 Filter/DN 片段的映射。
- 🔴 **CHECKPOINT C（转义策略确认）**：必须说明 RFC 转义与白名单策略是否生效。
- 🛑 **STOP**：若 Filter 可控性证据不闭合，结论降级为 `⚠️待验证`。

## 失败场景与兜底（if-then）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| LDAP 执行点明确但输入映射不清 | 补齐参数到 Filter/DN 片段映射 | 降级 `⚠️待验证` |
| RFC 转义策略无法验证 | 核对 4514/4515 编码实现与边界 | 不输出可利用强结论，仅给验证步骤 |
| 绑定模式与查询用途未区分 | 区分认证/搜索/同步场景分别评估 | 采用保守结论并保留待补证项 |

🔴 **STOP：任一兜底触发时，禁止输出“已确认注入”。**

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

- 反模式：只命中 LDAP API 就判注入。正确做法：证明输入进入 Filter/DN 关键片段。
- 反模式：忽略 RFC4515/4514 转义差异。正确做法：明确转义策略与绕过面。
- 反模式：不核对绑定模式与查询用途。正确做法：区分认证、搜索、同步不同风险语义。
- 反模式：证据不全就写“可利用”。正确做法：降级 `⚠️待验证`。

## 可执行参数与输出模板（强制）

- 审计结论等级：`已确认` / `⚠️待验证` / `不适用`（三选一，禁止留空）。
- 证据最小集：至少包含 `入口点`、`可控参数`、`关键调用`、`安全边界`、`缺失证据` 五项。
- 输出文件命名：统一使用 `{topic}_{timestamp}.md`，并与 `IO_PATH_CONVENTION.md` 对齐。
- 禁止使用软化措辞：如“可能有风险/建议关注/视情况而定/大概率”等；证据不足时必须明确写 `⚠️待验证` 与下一步补证动作。

最小输出片段（可直接复用）：

```md
- 命中ID：M{hash}（文件路径片段+行号+序号，用于跨阶段追踪和回归对齐）
- 审计结论等级：已确认
- 证据最小集：入口点=...；可控参数=...；关键调用=...；安全边界=...；缺失证据=无
- test_id：T{hash}（关联测试用例）
- 下一步动作：若存在缺口，补 trace_id=... 的参数传播证据
```
- 审计结论等级：已确认
- 证据最小集：入口点=...；可控参数=...；关键调用=...；安全边界=...；缺失证据=无
- 下一步动作：若存在缺口，补 trace_id=... 的参数传播证据
```

## 输出

- vuln_audit/ldap_{timestamp}.md
- 可选：vuln_poc/ldap_{timestamp}.md（已确认 / 待验证 / 环境依赖 PoC；如不适合直接构造请求，至少给出验证步骤）
