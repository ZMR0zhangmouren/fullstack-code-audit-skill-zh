---
name: dotnet-second-order-audit
description: .NET 二次注入审计。识别数据存储后二次触发的注入风险（存储型 XSS 的二次触发、SQL 注入的二次执行、文件操作的二次访问等），追踪存储入口到触发入口的数据流，输出分级、证据和修复建议。
---

# .NET 二次注入（Second-Order）审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖以下与 Second-Order 相关的共享抓手：
  - **入口定义抓手**：Controller Action、Minimal API Endpoint、SignalR Hub、BackgroundJob/HostedService
  - **敏感操作抓手**：SQL 执行、文件操作、命令执行、模板渲染、序列化操作
  - **业务执行抓手**：数据库写入、缓存写入、Session 存储、Cookie 存储、文件写入
  - **前置控制抓手**：Authorize、AllowAnonymous、ActionFilter、数据校验
- 若项目存在数据存储抽象层（Repository、UnitOfWork、Cache Service、Message Queue），必须补充到输出中的项目内抓手章节

## 输入依赖

- 必需：`source_path`
- 必需：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（用于对齐存储入口和触发入口的 route_id）
- 必需：`route_tracer/*_{timestamp}.md`（用于追踪存储到触发的完整数据流）
- 可选：`auth_audit/auth_mapping_{timestamp}.md`（用于补充存储入口和触发入口的鉴权状态差异）
- 可选：`framework_audit/*_{timestamp}.md`（用于补充 Session、Cache、BackgroundJob 配置）
- 本专项属于**跨入口 trace-gate 类型**，必须追踪存储入口到触发入口的完整数据流
- 需要同时分析 `route_mapping` 中的多个 route_id，发现存储-触发配对

## 重点检查

### 1. 存储型 XSS 的二次触发

- **存储入口**：用户输入写入数据库、Session、Cookie、缓存、文件
- **触发入口**：从存储后端读取并渲染到 View / JSON / HTML 响应
- 常见场景：
  - 用户资料（Profile）更新后，全局展示
  - 评论/帖子发布后，列表页批量展示
  - 消息通知渲染时，全局广播
  - 富文本编辑器保存后，未做 HTML 净化直接输出

### 2. SQL 注入的二次执行

- **存储入口**：用户输入写入数据库字段
- **触发入口**：该字段被用作后续 SQL 查询的一部分（而非参数绑定）
- 常见场景：
  - 动态列名/表名：从配置表读取列名拼接 SQL
  - 动态排序字段：Order By 参数来自数据库配置
  - 报表生成：数据库存储的 SQL 片段被再次执行
  - 动态筛选器：存储的过滤规则被直接拼接入 SQL

### 3. 命令注入的二次执行

- **存储入口**：文件名/路径写入数据库
- **触发入口**：该路径被用于 `Process.Start` 或 shell 执行
- 常见场景：
  - 文件处理队列：数据库存储的文件路径被后续 Job 读取执行
  - 图片处理：数据库存储的图片路径被 ImageMagick/FFmpeg 处理
  - 日志分析：数据库存储的日志文件路径被 tail/grep 处理

### 4. 文件操作的二次访问

- **存储入口**：用户上传文件，路径/内容写入数据库
- **触发入口**：路径被用于 `File.ReadAllText`、`PhysicalFile`、`StaticFiles`
- 常见场景：
  - 动态资源加载：从数据库读取文件路径后返回静态文件
  - 模板文件管理：数据库存储的模板路径被 Razor/Roslyn 加载
  - 配置热更新：数据库存储的配置路径被 Configuration 加载

### 5. 反射型漏洞的持久化

- **存储入口**：危险输入写入 Session/Cache/数据库
- **触发入口**：后续请求从存储中读取并触发危险操作
- 常见场景：
  - ViewState / 序列化对象持久化：存储的危险对象在后续请求被反序列化
  - 权限提升：缓存的角色/Claim 在后续请求被使用
  - 路径遍历：存储的文件路径在后续请求被访问

### 6. 消息队列/缓存二次处理

- **存储入口**：消息/缓存写入 Message Queue、Redis、MemoryCache
- **触发入口**：Consumer 从 Queue 读取并执行危险操作
- 常见场景：
  - 异步任务队列：存储的任务参数被 BackgroundJob 执行
  - 发布-订阅模式：存储的消息内容被多个订阅者处理
  - 缓存失效触发：存储的缓存键被 Dependency Injection 使用

### 7. 存储入口与触发入口配对分析

- **存储入口识别**：DB Write、Cache Set、File Write、Session Set
- **触发入口识别**：DB Read、Cache Get、File Read、Session Get
- **数据流追踪**：从存储点经过传播路径到触发点
- **信任边界差异**：存储入口是否需要鉴权 vs 触发入口是否需要鉴权

## 枚举规则（强制细化）

### 存储入口枚举

搜索关键字：
- `INSERT`, `UPDATE`, `SaveChanges`, `ExecuteSqlRaw`（写入场景）
- `Add`, `Update`, `Remove`（EF Core）
- `SetString`, `SetObject`（Redis）
- `Set`, `Add`（MemoryCache / IMemoryCache）
- `Session.SetString`, `Session.SetObject`
- `Response.Cookies.Append`（Cookie 写入）
- `File.WriteAllText`, `File.WriteAllBytes`, `CopyToAsync`
- `StreamWriter.Write`
- `JsonSerializer.Serialize`（写入场景）

枚举记录要求：
- 记录每个写入操作的入口 route_id
- 记录写入数据的来源（用户输入、计算生成、混合）
- 记录写入目标（数据库表/字段、缓存键、文件路径、Session 键）
- 记录是否缺少写入前的输入净化

### 触发入口枚举

搜索关键字：
- `SELECT`, `Query`, `FromSqlRaw`, `ExecuteSqlQuery`（读取场景）
- `Find`, `FirstOrDefault`, `SingleOrDefault`, `ToList`
- `GetString`, `GetObject`（Redis）
- `Get`, `TryGetValue`（MemoryCache）
- `Session.GetString`, `Session.GetObject`
- `Request.Cookies`
- `File.ReadAllText`, `File.ReadAllBytes`, `OpenRead`
- `StreamReader.Read`
- `JsonSerializer.Deserialize`

枚举记录要求：
- 记录每个读取操作的入口 route_id
- 记录读取后数据的流向（模板渲染、SQL 拼接、命令执行、文件访问、序列化）
- 记录读取后数据是否经过净化或参数化
- 记录触发时是否需要鉴权

### 存储-触发配对枚举

搜索关键字组合：
- 数据库表名（存储时写入的表 = 触发时读取的表）
- 缓存键模式（Cache Key Pattern）
- Session 键模式（Session Key Pattern）
- 文件路径模式（File Path Pattern）
- Message Queue Topic / Channel

枚举记录要求：
- 构建 存储入口 → 数据传播路径 → 触发入口 的完整链路
- 记录信任边界差异（存储入口鉴权状态 vs 触发入口鉴权状态）
- 记录数据是否经过中间转换或持久化
- 评估每个配对的可利用性

### 输入净化缺失枚举

搜索关键字：
- `Html.Raw`, `MarkupString`, `@Html.Raw`
- `innerHTML`, `textContent`
- `Dynamic` + SQL 片段拼接
- 字符串拼接 SQL（不在参数绑定中）
- `Process.Start` + 字符串路径
- `eval`, `Execute`, `DynamicExpression`

枚举记录要求：
- 记录每个未净化输入进入危险操作的组合点
- 记录净化函数的缺失或失效场景
- 评估净化缺失与存储-触发配对的关联

### 异步/后台处理枚举

搜索关键字：
- `BackgroundService`
- `IHostedService`
- `IConsumer`, `Handle`（MassTransit / MediatR）
- `Publish`（消息发布）
- `Enqueue`, `QueueBackgroundWorkItem`
- `Hangfire`, `Quartz`
- `IBackgroundTask`, `PeriodicTimer`
- `Channel<T>.Reader`

枚举记录要求：
- 记录后台 Job 的触发源（时间驱动、事件驱动、手动触发）
- 记录后台处理中读取的数据源（数据库、缓存、文件）
- 记录后台处理中的危险操作（SQL、命令、文件、模板）
- 评估消息队列中的危险数据流

## 证据引用

### 二阶数据链核心概念（新增）

二阶注入不是"存储后触发"这么简单。必须区分两个入口的不同责任：

| 入口类型 | 责任 | 验证问题 |
|---------|------|---------|
| `source_write_entry` | 危险数据从哪里来、是否受攻击者控制 | 攻击者能否通过真实写入边界控制它？ |
| `source_trigger_entry` | 什么时候读取、谁触发 | 保存后的值何时被读取？触发者是谁？ |

### 三层验证条件（强制）

每个二阶注入结论必须逐层验证以下三个条件：

**第一层：数据链成立**
- 攻击者可控制数据写入
- 写入路径可达持久化存储

**第二层：触发路径成立**
- 保存后的值沿执行路径到达 sink
- 触发入口的权限/身份与写入入口不同（信任边界差异）

**第三层：语法允许注入**
- 数据库/命令/模板语法允许闭合边界、重新进入结构
- 例如：SQL 允许反引号闭合、命令允许分隔符

### 证据点

- `EVID_SECOND_ORDER_STORAGE`：数据二次存储证据
- `EVID_SECOND_ORDER_TRIGGER`：二次触发执行证据
- `EVID_SECOND_ORDER_STORE_ENTRANCE`：存储入口点证据
- `EVID_SECOND_ORDER_TRIGGER_ENTRANCE`：触发入口点证据
- `EVID_SECOND_ORDER_DATA_FLOW_MAPPING`：存储到触发的数据流映射证据

### taint_nodes 分步记录（新增）

与 `DOTNET_ROUTE_OUTPUT_TEMPLATES.md` 的 `taint_nodes` 对齐，每个二阶链路必须记录：

```json
{
  "taint_nodes": [
    {
      "taint_type": "source_write_entry",
      "filepath": "Controllers/ConfigController.cs",
      "line_range": "45-48",
      "description": "用户通过 SaveFieldConfig 接口写入 column_key",
      "is_attacker_controllable": true,
      "write_permission": "business_config_manager"
    },
    {
      "taint_type": "storage_read",
      "filepath": "Services/SearchService.cs",
      "line_range": "30-33",
      "description": "从 field_config 表读取 column_key"
    },
    {
      "taint_type": "source_trigger_entry",
      "filepath": "Controllers/SearchController.cs",
      "line_range": "20-25",
      "description": "搜索请求触发读取配置表",
      "trigger_condition": "用户发起搜索请求",
      "trigger_permission": "anonymous_or_authenticated"
    },
    {
      "taint_type": "transfer",
      "filepath": "Services/SearchService.cs",
      "line_range": "40-44",
      "description": "column_key 被拼入 SQL 查询条件"
    },
    {
      "taint_type": "barrier",
      "line_range": "40-44",
      "barrier_type": "column_whitelist",
      "actual_behavior": "无白名单校验",
      "status": "FAILED"
    },
    {
      "taint_type": "sink",
      "filepath": "Services/SearchService.cs",
      "line_range": "45-48",
      "description": "SQL 执行：column_key 进入列标识符位置"
    }
  ]
}
```

## 失败与降级分支（强制，按三层验证条件）

| 触发条件 | 所属层级 | 一线处理 | 仍失败的兜底 |
|---|---|---|---|
| source_write_entry 无法证明攻击者可控 | 第一层 | 输出写入证据与权限边界分析 | 标记 `第一层不成立`，降级为 `⚠️待验证` |
| 数据写入后无法确认持久化成功 | 第一层 | 追踪存储介质写入确认 | 标记 `数据链未闭合`，降级为 `⚠️待验证` |
| source_trigger_entry 无法确认触发时机 | 第二层 | 输出触发证据与候选触发点 | 标记 `第二层不成立`，降级为 `⚠️待验证` |
| 存储与触发权限边界相同（无信任差异） | 第二层 | 输出权限对比分析 | 风险降级，不标记为越权二次注入 |
| 语法不允许闭合边界（如参数化查询） | 第三层 | 输出语法分析 | 标记 `第三层不成立`，排除注入可能 |
| 异步/队列消费链无法重建 | 跨层 | 输出投递点和消费点候选集合 | 明确"环境依赖/运行时依赖"，禁止已确认结论 |

🔴 **STOP：三层验证条件任一未满足时，禁止标记为已确认二次注入。**

### 三层验证判定矩阵

| 第一层 | 第二层 | 第三层 | 结论 |
|--------|--------|--------|------|
| ✅ 成立 | ✅ 成立 | ✅ 成立 | 🔴 已确认二次注入 |
| ✅ 成立 | ✅ 成立 | ❌ 不成立 | ⚠️ 待验证（语法未确认） |
| ✅ 成立 | ❌ 不成立 | - | ⚠️ 待验证（触发路径未闭合） |
| ❌ 不成立 | - | - | ⚠️ 待验证（写入边界未确认） |
| ⚠️ 部分 | ⚠️ 部分 | ⚠️ 部分 | ⚠️ 待验证（多层缺口） |

## Barrier 验证矩阵（强制，与三层验证互补）

本专项必须在三层验证基础上，对以下 barrier 类型执行验证，按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 标准评估：

| Barrier 类型 | 验证动作 | 判定标准 |
|-------------|---------|---------|
| **写入前净化** | 确认 `source_write_entry` 是否在写入持久化存储前执行了输入净化（如 HTML 编码、SQL 参数化、路径校验） | 有 fail-close 净化 → 第一层可能不成立；无净化或净化为 fail-open → 第一层成立 |
| **读取后净化** | 确认 `source_trigger_entry` 从存储读取后是否执行了二次净化 | 有 fail-close 二次净化 → 第三层可能不成立；无二次净化 → 需重点评估第三层 |
| **存储-触发信任边界差异** | 对比存储入口与触发入口的鉴权要求，确认是否存在信任边界差异 | 存储需高权限但触发低权限/匿名 → 🔴 高风险；权限相同 → 风险降级 |
| **持久化存储隔离** | 确认数据库/缓存/文件存储是否存在租户/用户隔离，攻击者数据是否可被目标用户触发 | 无隔离 → 🔴 高危；严格隔离 → 风险降级 |
| **后台任务执行权限** | 确认 BackgroundJob/Queue Consumer 的执行账户权限，是否高于 Web 入口 | 高权限执行 → 🔴 高危放大；同权限或更低 → 按正常评估 |
| **语法闭合验证（第三层）** | 确认目标 sink 的语法是否允许闭合边界、重新进入结构（如 SQL 反引号、HTML 标签闭合、命令分隔符） | 语法允许闭合 → 第三层成立；语法严格参数化 → 第三层不成立 |

🔴 **STOP：任一 barrier 验证为 `silent-fallback` 或 `fail-open` 时，禁止将结论标记为「已确认安全」或「误报」。**

## 二阶段判定（强制）

遵循 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

1. **阶段一（临时结论）**：对每条存储-触发配对先标记 `确认漏洞候选` / `待确认` / `误报`
2. **阶段二（强制追证）**：
   - 若阶段一为 `确认漏洞候选` → 必须完成三层验证 + Barrier 验证矩阵全部相关项，通过后才能标记 `已确认`
   - 若阶段一为 `待确认` → 必须向下追至少一跳调用链或下游解析器，直到可判定为止
   - 若阶段二仍无法闭合 → 保持 `待确认`，并明确记录缺失哪一层/哪一跳证据

## 测试建议（强制）

遵循 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的测试要求，对每个确认漏洞或待验证项给出：

- **正向测试**：构造二阶注入 PoC（步骤1：通过存储入口写入恶意数据；步骤2：通过触发入口触发执行），验证漏洞确实存在
  - 存储型 XSS：写入 `<script>alert(1)</script>`，触发页面查看
  - SQL 二阶注入：写入恶意列名，触发报表查询
  - 命令二阶注入：写入恶意路径，触发后台文件处理
- **负向测试**：构造被 barrier 拦截的输入（如写入前净化生效、读取后二次净化生效、语法不允许闭合），验证保护机制有效
- **回归测试**：修复后复测，确认 barrier 仍然生效，且未引入新的绕过路径

测试用例应标注 `test_id`，并在审计报告中与对应命中 ID 关联。

## 资源引用与可达性校验（强制）

- 必引共享索引：`skills/shared/DOTNET_AUDIT_GRABBER_INDEX.md`（抓手来源）与 `skills/shared/EVIDENCE_POINT_IDS.md`（证据口径）。
- 输出口径校验：落盘路径与命名必须对齐 `skills/shared/IO_PATH_CONVENTION.md`，不得自定义偏离目录。
- 证据一致性校验：若引用分级结论，需与 `skills/shared/SEVERITY_RATING.md` 保持一致。
- 可达性检查：提交前至少确认一次关键引用文件可访问（例如 `DOTNET_AUDIT_GRABBER_INDEX.md`、`IO_PATH_CONVENTION.md`）。

## 实测用例与通过标准（强制）

- 每个 skill 至少维护 2 个典型测试用例（happy path + 一条复杂场景），并在结果中标注用例 ID。
- 每轮评估至少 1 条用例执行 `full_test`；若受限只能 `dry_run`，必须记录 `dry_run_reason` 与补测计划。
- 通过标准至少同时满足：`意图达成`、`关键证据命中`、`输出格式合规`；任一不满足不得给出"通过"。

## 整体架构与冗余控制（强制）

- 章节组织必须保持三层骨架：`输入约束` → `执行步骤` → `输出与验收`，不得缺层或跨层混写。
- 单段建议不超过 6 行；同义规则禁止重复出现两次以上，重复内容需合并到唯一真源章节。
- 禁止 AI 腔与空话衔接词堆叠（如"首先/其次/最后/综上/说白了/换句话说"）；发现即改为可执行语句。

## 质量门禁与评估一致性（强制）

- 产出前必须执行最小门禁自检：`输入完整性`、`关键证据命中`、`输出路径合法` 三项全部为 PASS。
- 若存在 `关键证据缺失`、`链路未闭合`、`consistency_check_status=BLOCKED` 任一条件，结论必须降级为 `BLOCKED`，禁止输出"确认可利用/可交付"。
- 报告中必须显式记录：`gate_status`、`blocked_reasons`、`recheck_action`，并与 `quality/*` 产物可回溯对齐。

## 不要做的事（反例黑名单）

| # | 反模式 | 为什么不要做 | 正确做法 |
|---|---|---|---|
| 1 | 只找到存储点就下漏洞结论 | second-order 必须三层验证全部满足 | 同时验证 source_write_entry、source_trigger_entry 和语法允许 |
| 2 | 忽略 source_write_entry 与 source_trigger_entry 的权限差异 | 风险强度会被高估或低估 | 记录权限/租户边界差异，评估信任边界转移 |
| 3 | 忽略异步消费链 | 真实触发常在后台任务 | 必须列投递-消费链路 |
| 4 | 不验证语法是否允许注入 | 即使数据可控且路径可达，语法不允许也无法注入 | 确认数据库/命令/模板语法允许闭合边界 |
| 5 | 将 source_write_entry 和 source_trigger_entry 混为一谈 | 写入者≠触发者，责任不同 | 分开记录、分别验证 |
| 6 | 只看到存储→读取→sink 就认为二阶成立 | 缺少触发入口的独立验证 | 必须验证触发入口的触发条件与触发者身份 |

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按"共享抓手索引 → 本专项枚举规则 → 证据点引用"顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件"输出"章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（source_write_entry 确认）**：必须确认攻击者能否通过真实写入边界控制数据，记录写入权限与攻击面。
- 🔴 **CHECKPOINT B（storage_read 确认）**：必须确认数据从持久化存储成功读取，记录读取路径与中间传播节点。
- 🔴 **CHECKPOINT C（source_trigger_entry 确认）**：必须确认触发入口的权限/身份与写入入口不同（信任边界差异），记录触发条件与触发者。
- 🔴 **CHECKPOINT D（语法允许确认）**：必须确认数据库/命令/模板语法允许闭合边界、重新进入结构（如 SQL 反引号闭合）。
- 🛑 **STOP**：若三层验证条件任一未满足，不得下"二次注入不成立"或"已确认二次注入"结论，只能标记为 `⚠️待验证`。

## 可执行参数与输出模板（强制）

- 审计结论等级：`已确认` / `⚠️待验证` / `不适用`（三选一，禁止留空）。
- 证据最小集：至少包含 `入口点`、`可控参数`、`关键调用`、`安全边界`、`缺失证据` 五项。
- 输出文件命名：统一使用 `{topic}_{timestamp}.md`，并与 `IO_PATH_CONVENTION.md` 对齐。
- 禁止使用软化措辞：如"可能有风险/建议关注/视情况而定/大概率"等；证据不足时必须明确写 `⚠️待验证` 与下一步补证动作。

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

- vuln_audit/second-order_{timestamp}.md
- vuln_poc/second-order_{timestamp}.md（已确认 / 待验证 / 环境依赖 PoC）

### 输出文件结构

```
vuln_audit/second-order_{timestamp}.md
├── # 二次注入审计报告
├── ## 摘要
│   ├── 发现数量
│   ├── 高危项列表
│   └── 存储-触发配对统计
├── ## 存储-触发配对分析
│   ├── 配对列表（存储入口、触发入口、危险类型、route_id）
│   ├── 信任边界差异评估
│   ├── 可利用性评估
│   └── taint_nodes 分步记录（每个配对必须包含完整 taint_nodes JSON）
├── ## 存储型 XSS 二次触发
│   ├── 配对详情（含 taint_nodes）
│   ├── 数据流路径
│   └── 风险评级
├── ## SQL 二次注入
│   ├── 配对详情（含 taint_nodes）
│   ├── 动态列名/表名分析
│   └── 风险评级
├── ## 命令二次注入
│   ├── 配对详情（含 taint_nodes）
│   ├── 文件路径传播路径
│   └── 风险评级
├── ## 文件操作二次访问
│   ├── 配对详情（含 taint_nodes）
│   ├── 路径传播路径
│   └── 风险评级
├── ## 反射型漏洞持久化
│   ├── 配对详情（含 taint_nodes）
│   ├── 反序列化链路
│   └── 风险评级
├── ## 消息队列/缓存二次处理
│   ├── 配对详情（含 taint_nodes）
│   ├── 异步数据流
│   └── 风险评级
├── ## 异步/后台处理分析
│   ├── BackgroundJob 列表
│   ├── 触发源分析
│   └── 危险操作评估
├── ## 项目内抓手补充
│   ├── 私有封装
│   ├── 数据访问层
│   └── 消息队列配置
└── ## 修复建议
    ├── 输入净化强化
    ├── 数据隔离建议
    ├── 异步处理安全加固
    └── 监控与告警建议
```

### vuln_poc 结构

```
vuln_poc/second-order_{timestamp}.md
├── # 二次注入 PoC 模板
├── ## 存储型 XSS PoC
│   ├── 步骤1：存储阶段（route_id + 请求模板）
│   ├── 步骤2：触发阶段（route_id + 请求模板）
│   └── 预期结果
├── ## SQL 二次注入 PoC
│   ├── 步骤1：写入恶意列名
│   ├── 步骤2：触发查询
│   └── 预期结果
├── ## 命令二次注入 PoC
│   ├── 步骤1：存储恶意路径
│   ├── 步骤2：触发命令执行
│   └── 预期结果
├── ## 消息队列二次处理 PoC
│   ├── 步骤1：发布恶意消息
│   ├── 步骤2：触发消费处理
│   └── 预期结果
└── ## 验证方法
    └── 测试步骤
```
