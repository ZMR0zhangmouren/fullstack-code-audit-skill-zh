---
name: dotnet-signalr-audit
description: SignalR 框架专项审计工具。针对 Hub 方法授权、组管理、连接状态、参数验证与跨连接消息边界进行白盒审计。
---

# SignalR 框架专项审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与 signalr 相关的入口定义、绑定转换、前置控制、敏感操作、安全配置抓手
- 若项目存在框架二次封装、统一扩展方法、平台基座或宿主包装层，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（如已由 `dotnet-route-mapper` 生成，用于对齐 Hub 方法、参数来源与 `route_id`）
- 可选：`auth_audit/auth_mapping_{timestamp}.md`（如需对齐连接建立、Hub 授权和租户/房间边界）
- 可选：`route_tracer/{route_id}/trace_{timestamp}.md` 与 `route_tracer/{route_id}/trace_summary_{timestamp}.md`（如需把 Hub 方法与下游数据库、文件、模板、通知等副作用链做交叉引用）

## 重点检查

- Hub 方法上的 [Authorize] / policy / role / claim 检查、IUserIdProvider、自定义 HubFilter、连接建立时的 claims 映射与权限校验
- Group 加入/退出、广播目标、租户隔离、房间边界、Presence 状态与跨连接消息可见性
- ConnectionId、UserIdentifier、Context.Items、查询字符串令牌、Cookie flags / JWT validation parameters 与 access token 的绑定关系
- 客户端消息参数校验、模型绑定、流式上传、二进制消息和重试机制对服务端副作用的影响
- Backplane、Redis、Azure SignalR、sticky session、Scale-out 与连接迁移导致的授权和状态一致性问题
- Hub 方法是否会触发数据库、文件、命令、模板、通知等高价值操作且缺少额外约束

## 枚举规则（强制细化）

- 枚举所有 Hub、Hub 方法、HubFilter、IUserIdProvider、OnConnectedAsync、OnDisconnectedAsync、Group 管理逻辑与客户端回调方法
- 优先搜索 Hub、SendAsync、Groups.AddToGroupAsync、Clients.All、Clients.User、Clients.Group、Authorize、HubFilter、Context.UserIdentifier、access_token
- 枚举连接建立参数、查询字符串令牌、Cookie 认证、Claims 映射、Group 名构造、租户标识拼接和房间加入条件
- 枚举服务端副作用方法：数据库写入、文件操作、任务下发、通知推送、模板渲染、管理动作，记录其是否只依赖连接态而未做业务鉴权
- 对每个 Hub 方法记录：调用方向、参数来源、授权方式、目标广播范围、状态依赖、scale-out 影响与后续副作用

## Barrier 验证矩阵（强制）

按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 三级标准评估：

| 等级 | 检查项 | 通过标准 | 失败降级 |
|------|--------|----------|----------|
| 一级 | Hub 方法存在且连接可建立 | 存在 Hub 方法、OnConnectedAsync 且客户端可实际建立连接并调用 | BLOCKED → 无用户可达的 Hub 入口，专项降为低优先级 |
| 二级 | 授权/组管理存在绕过 | Hub 方法/Group 加入缺少 [Authorize] 或 policy 检查，或 UserIdentifier/Claims 映射可被伪造 | BLOCKED → 授权与组管理完整无绕过，结论降级 |
| 三级 | 广播/副作用未授权可达 | SendAsync/Clients.All/Group 广播未做业务鉴权，或 Hub 方法触发数据库/文件/命令等高价值操作 | PARTIAL → 仅输出潜在风险与验证步骤 |

## 二阶段判定流程（强制）

- **阶段 1（初筛命中）**：命中 Hub 方法/连接建立 + 授权/组管理 + 广播/副作用链，输出 `命中ID：M{hash}`。
- **阶段 2（精筛确认）**：
  1. 逆向追踪 连接建立 → Claims 映射 → Hub 方法授权 链路；
  2. 验证 Group 加入条件、UserIdentifier 实现与 Claims 映射的可伪造性；
  3. 评估广播范围（Clients.All/Group/User）与下游副作用（数据库/文件/命令）的授权边界；
  4. 若三级 Barrier 全部通过 → `确认漏洞`；任一失败 → 按矩阵降级。

## 判定规则与优先级（强制）

1. **确认漏洞**：Hub 入口可达 + 授权/组管理绕过 + 广播/副作用未授权。输出 `确认漏洞`。
2. **待确认**：Hub/授权/广播证据部分存在，但 scale-out/Backplane 或 Claims 映射不可证实。输出 `待确认`。
3. **误报/无风险**：Hub 方法均授权、组管理严格、广播范围可控、下游副作用有业务鉴权。输出 `误报` 并给出判定依据。

## 测试建议与最小触发条件（强制）

- **最小触发条件**：
  - 存在 SignalR Hub 或 Hub 方法
  - 客户端可建立连接并调用 Hub 方法
  - 或 Hub 方法/Group 缺少授权检查
  - 或广播/副作用未做业务鉴权
- **测试用例建议**：
  - Happy Path：正常连接建立与 Hub 调用，授权与广播范围正确
  - 边界/歧义：查询字符串令牌伪造、Group 名注入、Backplane 状态不一致、Scale-out 连接迁移授权漂移
- 每条命中输出追加 `命中ID：M{hash}` 和 `test_id：T{hash}`，用于回溯。

## 工作流（输入→执行→输出）

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（Hub入口确认）**：必须确认 Hub 方法、分组与连接协商入口完整。
- 🔴 **CHECKPOINT B（身份与授权确认）**：必须确认连接态鉴权与方法级授权链。
- 🔴 **CHECKPOINT C（消息边界确认）**：必须确认客户端回推数据到下游处理的边界。
- 🛑 **STOP**：若连接鉴权链未闭合，不得给出“可安全上线”结论。

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

- 输出文件：framework_audit/signalr_{timestamp}.md
- 必须按 连接建立与身份、Hub 方法与参数、组与广播边界、scale-out 与状态一致性 四个章节组织结果
- 每个问题点必须写明 Hub 方法名、授权元数据、客户端可控参数、广播目标、下游副作用
- 必须单列 查询字符串令牌、Cookie 认证、access token 回退、Backplane/Azure SignalR 差异 等环境依赖项

## 证据引用

- EVID_AUTH_PATH_PROTECTED_MATCH
- EVID_AUTH_PERMISSION_CHECK_EXEC
- EVID_LOGIC_STATE_TRANSITION
- EVID_SESS_COOKIE_FLAGS

## 失败与降级分支（强制）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| Hub 方法可达但鉴权链不完整 | 输出方法级授权与连接态证据 | 降级为 PARTIAL，禁止越权已确认结论 |
| Group 广播边界无法验证（多节点/Backplane） | 记录单节点证据与组键构造 | 标记 `⚠️环境依赖` 并待联调补证 |
| UserIdentifier 映射实现不可解析 | 列候选实现与注册点 | 无法收敛时保留候选链并降级 |
| 仅见 SendAsync 无业务副作用闭合 | 输出广播路径与影响面 | 不输出高危结论，转待验证 |

🔴 **STOP：未证明“连接身份→Hub方法→目标广播/副作用”闭合时，禁止输出已确认越权。**

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
| 1 | 见 Hub 就默认高风险 | 关键在授权和目标边界 | 必须给出鉴权与广播范围证据 |
| 2 | 忽略 scale-out 场景 | 单节点结论可能失真 | 分别标注单节点与多节点语义 |
| 3 | 把连接态当业务授权 | 易产生误判越权 | 连接授权与业务授权分开核验 |

输出类型映射：AUTH、LOGIC、XSS、CFG。
