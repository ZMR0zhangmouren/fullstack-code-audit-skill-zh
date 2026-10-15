---
name: dotnet-crlf-audit
description: .NET CRLF 与响应分割审计工具。识别 Response.Headers、Set-Cookie、Location 等输出点中的控制字符注入风险。
---

# .NET CRLF 审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与 Header、Cookie、日志换行、响应分割和代理透传相关的共享抓手
- 若项目存在 ResponseHelper、HeaderBuilder、CookieManager、LogFormatter 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（用于对齐输出入口、参数来源与 `route_id`）
- 可选：`framework_audit/*_{timestamp}.md`（用于补充宿主服务器、代理边界与响应处理控制面）
- trace-gate 场景下优先消费：`route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline` 执行，当前专项引用的 `route_id` 应与 `cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- Response.Headers.Append / Add 中值来源为用户输入的位置
- Set-Cookie 值、Location 头、Content-Disposition 文件名中的用户可控内容
- 代理透传头（X-Forwarded-*）未过滤直接写入响应
- 下载文件名从数据库或请求参数获取且未过滤 \r\n 的场景
- 自定义安全头中嵌入用户数据的位置
- 宿主服务器（Kestrel/IIS/Nginx）对 CRLF 的默认拦截行为与绕过可能

## 证据引用

- EVID_CRLF_OUTPUT_POINT
- EVID_CRLF_USER_INPUT_INTO_HEADER_COOKIE
- EVID_CRLF_CONTROL_CHAR_FILTERING_ENCODING

## 枚举规则（强制细化）

- 枚举所有 Response.Headers 写入、Set-Cookie、Location、Content-Disposition、自定义下载和反向代理透传 header 逻辑
- 优先搜索 HeaderDictionary、Append、Add、SetCookieHeaderValue、FileDownloadName、redirect location 等关键调用
- 枚举来自用户输入、文件名、日志 ID、代理头、数据库字段进入 header 的位置
- 对每个 header 输出点记录：字段名、值来源、过滤逻辑、宿主服务器拦截行为、可能造成的响应污染类型

证据建议：重点记录输出点、用户输入映射和控制字符过滤行为。

## Barrier 验证矩阵（强制）

按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 三级标准评估：

| 等级 | 检查项 | 通过标准 | 失败降级 |
|------|--------|----------|----------|
| 一级 | 输出点存在且用户输入可达 | Response.Headers/Set-Cookie/Location/Content-Disposition 输出点存在且值来源包含用户输入 | BLOCKED → 无用户输入映射，专项结束 |
| 二级 | 控制字符可注入 | `\r\n` 等控制字符未被有效过滤或编码，可到达输出点 | BLOCKED → 结论降级为 `⚠️待验证/环境依赖` |
| 三级 | 代理/宿主不拦截 | Kestrel/IIS/反代对含控制字符的 header 无默认拦截，或拦截可被绕过 | PARTIAL → 仅输出环境依赖结论与复现建议 |

## 二阶段判定流程（强制）

- **阶段 1（初筛命中）**：命中 header/cookie/location 输出点 + 用户输入映射，输出 `命中ID：M{hash}`。
- **阶段 2（精筛确认）**：
  1. 逆向追踪 输入 → header值 → 控制字符过滤 链路；
  2. 验证原始值、一次解码、二次解码后的控制字符残留；
  3. 检查 Kestrel/IIS/代理层默认拦截行为；
  4. 若三级 Barrier 全部通过 → `确认漏洞`；任一失败 → 按矩阵降级。

## 判定规则与优先级（强制）

1. **确认漏洞**：输出点存在 + 用户输入直达 + 控制字符未过滤 + 代理/宿主不拦截。输出 `确认漏洞`。
2. **待确认**：输出点与用户输入映射存在，但过滤逻辑或代理行为证据不足。输出 `待确认`。
3. **误报/无风险**：输出点无用户输入映射，或控制字符被有效过滤且代理层严格拦截。输出 `误报` 并给出判定依据。

## 测试建议与最小触发条件（强制）

- **最小触发条件**：
  - 存在 header/cookie/location 输出点
  - 输出值包含用户可控输入（请求参数、文件名、代理头、数据库字段）
  - `\r\n` 等控制字符可未过滤地到达输出点
- **测试用例建议**：
  - Happy Path：正常 header 值输出正确，含 `\r\n` 的请求被拦截或过滤
  - 边界/歧义：双重编码绕过、Unicode 换行符（`\u2028`/`\u2029`）、代理透传头注入
- 每条命中输出追加 `命中ID：M{hash}` 和 `test_id：T{hash}`，用于回溯。

## 工作流（输入→执行→输出）

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（输出点确认）**：必须先确认 header/cookie/location 的真实写出点。
- 🔴 **CHECKPOINT B（字符链确认）**：必须给出 `输入 -> header值 -> 控制字符过滤` 三段证据。
- 🔴 **CHECKPOINT C（代理语义确认）**：必须注明 Kestrel/IIS/代理层对非法 header 的处理差异。
- 🛑 **STOP**：若仅有关键字命中而无输出映射证据，结论降级为 `⚠️待验证`。

## 失败场景与兜底（if-then）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| 无法闭合输入到 header/cookie 输出映射 | 补齐参数来源到输出 API 的链路证据 | 降级 `⚠️待验证`，保留可疑点 |
| 控制字符过滤与解码路径不一致 | 同时验证原始值、一次解码和二次解码 | 按最不利路径保守评估，不给强结论 |
| 代理/宿主拦截行为不明确 | 区分 Kestrel、IIS、反代逐层记录 | 仅输出环境依赖结论与复现建议 |

🔴 **STOP：任一兜底触发时，禁止输出“CRLF 不成立”。**

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

- 反模式：把 header 写入点命中直接等同漏洞成立。正确做法：补齐输入映射与控制字符过滤证据。
- 反模式：忽略编码与双重解码路径。正确做法：同时验证原始值与解码后值。
- 反模式：不区分宿主/代理默认拦截能力。正确做法：明确部署链路的真实行为。
- 反模式：证据不足写“无风险”。正确做法：降级 `⚠️待验证`。

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

- vuln_audit/crlf_{timestamp}.md
- 可选：vuln_poc/crlf_{timestamp}.md（已确认 / 待验证 / 环境依赖 PoC；如不适合直接构造请求，至少给出验证步骤）
