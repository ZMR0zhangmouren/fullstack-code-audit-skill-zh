---
name: dotnet-mvc-audit
description: ASP.NET MVC 框架专项审计工具。针对 Controller、ModelBinder、Razor View、HtmlHelper、ActionFilter 和传统认证授权模式进行白盒审计。
---

# ASP.NET MVC 框架专项审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与 mvc 相关的入口定义、绑定转换、前置控制、敏感操作、安全配置抓手
- 若项目存在框架二次封装、统一扩展方法、平台基座或宿主包装层，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（如已由 `dotnet-route-mapper` 生成，用于对齐 Action 入口、绑定源与 `route_id`）
- 可选：`auth_audit/auth_mapping_{timestamp}.md`（如需对齐匿名入口、P0/P1 分桶与过滤器授权边界）
- 可选：`route_tracer/{route_id}/trace_{timestamp}.md` 与 `route_tracer/{route_id}/trace_summary_{timestamp}.md`（如需把 View/Redirect/File 等返回链与具体副作用路径做交叉引用）

## 重点检查

- Controller / Action 级鉴权、全局过滤器、Area、ChildAction、FilterAttribute 与自定义 ActionFilter 的覆盖关系
- Model Binding、TryUpdateModel、Bind/BindNever、FromForm、JSON Patch、上传模型与 over-posting 风险
- Razor Raw / HtmlString、Layout、Partial、EditorTemplate、DisplayTemplate、TagHelper、ViewComponent，以及 Controller Content / Json / 手工拼接 HTML / JS 的输出边界
- TempData、ViewBag、ViewData、ModelState、ReturnUrl、局部视图组合、错误页与重定向链中的信任边界
- Anti-forgery、OutputCache、FileResult、Content-Disposition 下载名、内容协商与异常过滤器的安全影响
- 传统 ASP.NET MVC 与 ASP.NET Core MVC 混合项目中的配置漂移和兼容层问题

## 枚举规则（强制细化）

- 枚举所有 Controller、Area、Action、ChildAction、Partial 渲染点、ViewComponent 以及自定义 FilterAttribute，记录其路由来源、鉴权元数据和视图渲染目标
- 优先搜索 Controller、ActionResult、TryUpdateModel、UpdateModel、Bind、BindNever、ValidateAntiForgeryToken、Html.Raw、HtmlString、Redirect、LocalRedirect、RedirectToAction、Content、Json、File、PartialView
- 枚举 ModelBinder、ValueProvider、ModelState 修改点、上传模型、复杂对象绑定、集合绑定和 JSON Patch 入口，记录哪些字段可由客户端直接覆盖
- 枚举 Razor View、Layout、Partial、EditorTemplate、DisplayTemplate、HtmlHelper、自定义 TagHelper 与 ViewBag/ViewData/TempData 数据注入点，记录输出编码与信任边界
- 对每个 Action 记录：入口路由、绑定来源、前置过滤器、视图/返回类型、状态变更能力、是否依赖传统配置或兼容层

## Barrier 验证矩阵（强制）

按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 三级标准评估：

| 等级 | 检查项 | 通过标准 | 失败降级 |
|------|--------|----------|----------|
| 一级 | Controller/Action 入口存在且映射完整 | 存在未授权或匿名可达的 Controller/Action，且路由映射完整可触发 | BLOCKED → 所有入口均有授权覆盖且映射完整，专项降为低优先级 |
| 二级 | 绑定/过滤器链存在绕过 | ModelBinding、TryUpdateModel、Bind/BindNever 等存在 over-posting 或字段覆盖绕过 | BLOCKED → 绑定链完整且过滤器无绕过，结论降级 |
| 三级 | 视图/返回面存在输出安全问题 | Razor Raw/HtmlString/Content/Json/File 等返回面存在未编码输出或敏感信息泄露 | PARTIAL → 仅输出潜在风险与验证步骤 |

## 二阶段判定流程（强制）

- **阶段 1（初筛命中）**：命中 Controller/Action 入口 + 绑定/过滤器链 + 输出面，输出 `命中ID：M{hash}`。
- **阶段 2（精筛确认）**：
  1. 逆向追踪 Controller/Action → 过滤器链 → 授权策略 链路；
  2. 验证 ModelBinding、TryUpdateModel、Bind/BindNever 的 over-posting 或字段覆盖条件；
  3. 评估 Razor/Content/Json/File 等返回面的编码边界与敏感信息泄露；
  4. 若三级 Barrier 全部通过 → `确认漏洞`；任一失败 → 按矩阵降级。

## 判定规则与优先级（强制）

1. **确认漏洞**：入口未授权可达 + 绑定/过滤器绕过 + 返回面存在安全问题。输出 `确认漏洞`。
2. **待确认**：入口/绑定/输出面证据部分存在，但授权链或编码上下文不可证实。输出 `待确认`。
3. **误报/无风险**：所有入口均有授权覆盖，绑定链完整无绕过，返回面编码正确。输出 `误报` 并给出判定依据。

## 测试建议与最小触发条件（强制）

- **最小触发条件**：
  - 存在 ASP.NET MVC Controller/Action
  - 存在未授权或匿名可达的入口
  - 或 ModelBinding/过滤器链存在 over-posting/绕过
  - 或返回面存在未编码输出/敏感信息泄露
- **测试用例建议**：
  - Happy Path：正常请求经完整过滤器链处理，授权与绑定正确
  - 边界/歧义：ChildAction/Area 过滤器覆盖差异、BindNever 与 over-posting、Razor 编码上下文切换
- 每条命中输出追加 `命中ID：M{hash}` 和 `test_id：T{hash}`，用于回溯。

## 工作流（输入→执行→输出）

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（控制器映射确认）**：必须确认 Controller/Action 与路由映射完整。
- 🔴 **CHECKPOINT B（绑定与过滤确认）**：必须确认 ModelBinding、过滤器与授权链生效。
- 🔴 **CHECKPOINT C（输出面确认）**：必须确认 View/Redirect/File 等返回面安全边界。
- 🛑 **STOP**：若映射与授权链未闭合，结论降级为 `⚠️待验证`。

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

- 输出文件：framework_audit/mvc_{timestamp}.md
- 必须按 入口与过滤器、模型绑定与字段覆盖、视图输出与编码边界、重定向/下载/缓存 四个章节组织结果
- 每个条目必须写明 Action 标识、视图或返回类型、关键绑定字段、前置过滤器、潜在影响类别
- 对兼容层或传统 MVC 专有风险必须单列 版本/宿主依赖，避免与 ASP.NET Core MVC 混淆

## 证据引用

- EVID_AUTH_TOKEN_DECODE_JUDGMENT
- EVID_AUTH_PERMISSION_CHECK_EXEC
- EVID_XSS_OUTPUT_POINT
- EVID_CSRF_TOKEN_VERIFY

## 失败与降级分支（强制）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| Action 入口可见但过滤器链不完整 | 输出已知过滤器与路由证据 | 标记 PARTIAL 并列出缺失过滤器证据 |
| 绑定风险存在但字段覆盖范围不明 | 记录可见 DTO 字段与绑定来源 | 降级为待验证，禁止 over-posting 已确认结论 |
| 输出点存在但编码上下文不完整 | 输出 Razor/返回类型与输出点 | 仅给潜在风险，不给强结论 |
| 兼容层（旧 MVC / Core）边界不清 | 分环境列证据并给差异假设 | 结论降级为环境依赖 |

🔴 **STOP：过滤器、绑定、输出三链任一缺失时，不得输出“已确认可利用”结论。**

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
| 1 | 只看 Controller 不看 View/Filter | 证据链会断裂 | 同时覆盖入口、过滤器、输出 |
| 2 | 把 HTML 输出问题一律归 XSS 高危 | 上下文与编码决定强度 | 标注上下文并分级 |
| 3 | 忽略 Anti-forgery 条件分支 | 易误判 CSRF 结论 | 明确记录 token 校验分支 |

输出类型映射：AUTH、XSS、LOGIC、CFG、CSRF。
