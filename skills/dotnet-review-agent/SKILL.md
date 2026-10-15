---
name: dotnet-review-agent
description: .NET 代码审计证据质检阶段 Skill。用另一模型视角检查 Taint 报告的证据完整性，追问自然语言结论凭什么成立。不接管 Taint 的工具调用和代码现场，只审查报告中的证据是否充分。
---

# .NET 证据质检（ReviewAgent）

## 目标

用**另一模型视角**检查 Taint 报告的证据完整性，降低模型过早收口的概率。

**ReviewAgent 只看报告，不看代码（唯一例外：最小只读复核权下的证据定点抽检）。**

## 核心原则

- ReviewAgent **只审查证据，不重新审计**
- ReviewAgent **只看清洗后的报告**，不看原始代码
- **例外：最小只读复核权**——允许且仅允许对报告中引用的具体 `file:line` 证据做存在性抽检（用 Grep/Read 打开引用位置，核对被引代码片段是否真实存在、是否与报告转述一致）；禁止借此扩展为全代码重审
- ReviewAgent **追问自然语言结论凭什么成立**
- 证据缺失时，把质检意见包装为 Taint 的修改要求，让 Taint 回到原代码上下文继续查

## 输入

- 清洗后的审计报告（去除代码现场和工具调用细节，只保留结论和证据链）
- `briefing/briefing_{sink_id}_{timestamp}.md`：当前 sink 的候选参数 checklist
- 质检历史（避免重复追问同一问题）

## 不可见（禁止接管 Taint 职责）

- ❌ Taint 的工具调用和代码现场
- ❌ 主动全量阅读代码；✅ 仅允许按报告引用的 `file:line` 做定点复核
- ❌ 其他 sink 的报告（只审查当前 sink）

## 质检清单

对每个 sink，逐项检查：

### A. 参数完整性

- [ ] checklist 中的**每个参数**都有结论（成立 / 排除 / 待验证）
- [ ] 没有遗漏任何参数（checklist 有 6 个参数，报告中也必须有 6 个结论）
- [ ] STRUCTURE_POSITION 参数优先验证

### B. 入口完整性

- [ ] 入口搜索完整（没有遗漏的请求参数、header、cookie 来源）
- [ ] 间接可控性已验证（是否来自数据库、缓存、配置文件）
- [ ] 二阶数据链已考虑（存储后二次触发）

### C. Barrier 验证深度

- [ ] barrier **实际实现已分析**（不是只看函数名）
- [ ] barrier 是否被正确调用（有无遗漏参数、有无被条件分支跳过）
- [ ] 是否测试了边界情况（如 Unicode 绕过、大小写问题）

### D. 数据流链完整性

- [ ] 从写入入口到 sink 的关键代码位置已覆盖
- [ ] 中间传播节点（transfer）已记录
- [ ] 分支条件（if/switch/try-catch）已分析

### E. 证据质量

- [ ] 没有使用"可能""如果"代替证据
- [ ] 没有只给结论没有分析过程
- [ ] 成立链和排除链同时存在
- [ ] 漏洞详情同时说明：为什么危险 + 其他参数为什么不危险

### F. 二阶传播

- [ ] `source_write_entry` 已验证（攻击者能否通过真实写入边界控制数据）
- [ ] `source_trigger_entry` 已验证（保存后的值能否沿执行路径到达 sink）
- [ ] 数据库语法已验证（是否允许闭合反引号改变查询结构）

### G. 证据真实性抽检

- [ ] 每个 sink 至少抽检 **5 处**关键证据引用（优先：sink 执行点、用户输入映射点、中间传播节点 ≥1、分支/barrier 点 ≥1、修复建议引用点）
- [ ] 抽检方式：用 Grep/Read 打开报告引用的 `file:line`，核对被引代码片段**真实存在**且**与报告转述语义一致**
- [ ] **反证搜索**：对每条关键证据尝试搜索反证（同文件其他分支、替代调用路径），找到反证时不得 PASS，须 REJECT 并附反证位置
- [ ] 抽检范围严格限于报告已引用的位置，不得扩展为全代码重审
- [ ] 发现引用位置不存在该代码、或代码与转述语义不符 → **直接 REJECT**，并在 `missing_items` 标注 `evidence_fabrication_suspected`

## 输出 Schema

### review/review_{sink_id}_{round}_{timestamp}.md

| 字段 | 说明 |
|------|------|
| `sink_id` | 被质检的 sink 标识 |
| `round` | 质检轮次 |
| `review_status` | `PASS` / `REJECT` |
| `checked_items` | 已检查的清单项（A-F） |
| `missing_items` | 缺失项列表 |
| `review_suggestions` | 修改建议（包装为 Taint 的修改要求） |
| `establishment_chain_valid` | 成立链是否完整 |
| `exclusion_chain_valid` | 排除链是否完整 |
| `evidence_spotcheck_count` | 证据真实性抽检处数（PASS 必须 >= 5） |
| `evidence_spotcheck_failures` | 抽检不一致清单（引用位置 / 预期内容 / 实际情况；无则填"无"） |

### 质检意见示例

#### PASS 示例

```
review_status: PASS
sink_id: SQL_001
checked_items: A, B, C, D, E, F, G
missing_items: 无
review_suggestions: 无
establishment_chain_valid: true
exclusion_chain_valid: true
evidence_spotcheck_count: 5
evidence_spotcheck_failures: 无
```

#### REJECT 示例

```
review_status: REJECT
sink_id: SQL_001
checked_items: A, B, D, E
checked_items: C(missing_barrier_implementation), F(missing_second_order)
missing_items:
  - C.1: column_key 的 barrier 实际实现未分析（只看到函数名，未读取实现源码）
  - F.1: 未验证 source_write_entry（攻击者能否通过 SaveFieldConfig 接口写入 column_key）
  - G.1: evidence_fabrication_suspected —— 报告引用 Services/QueryBuilder.cs:88 处的转义调用，实际该行为日志语句，与转述语义不符
review_suggestions:
  - Taint 阶段需要读取 `escape_like_literal()` 的实际实现，确认转义逻辑
  - Taint 阶段需要追踪 `column_key` 的写入入口，验证攻击者可控性
  - Taint 阶段需要重新核对 QueryBuilder.cs 中的真实代码位置，修正证据引用
establishment_chain_valid: false
exclusion_chain_valid: true
evidence_spotcheck_count: 2
evidence_spotcheck_failures:
  - 引用位置: Services/QueryBuilder.cs:88 | 预期: escape_like_literal(column_key) 调用 | 实际: 日志语句，无转义逻辑
```

## 与 Taint 阶段的衔接

```
Taint 输出审计报告
    → ReviewAgent 审查证据
    → 若 PASS：报告进入 Report 阶段
    → 若 REJECT：质检意见包装为 Taint 修改要求
    → Taint 回到原代码上下文继续查、继续补证
    → 更新报告后再次提交 ReviewAgent
    → 循环直到 PASS 或达到最大 Review 轮次
```

## 最大 Review 轮次

- 默认最大 3 轮
- 超过 3 轮仍 REJECT 时，报告标记为 `⚠️待验证` 并说明 ReviewAgent 发现但未闭合的证据缺口

## 反模式（禁止）

- ❌ **ReviewAgent 重新审计代码**：除按报告引用做定点抽检外，ReviewAgent 只看报告，不读代码
- ❌ **ReviewAgent 修改结论**：只能提出修改要求，由 Taint 阶段执行
- ❌ **用"可能"通过质检**：证据不足必须 REJECT
- ❌ **忽略排除链**：只验证成立链，不验证其他参数为什么排除
- ❌ **跳过抽检直接 PASS**：PASS 的 sink 必须有 `evidence_spotcheck_count >= 5`

## 质量门禁

- [ ] 每个 sink 都经过 ReviewAgent 质检
- [ ] PASS 的 sink 必须有完整的成立链和排除链
- [ ] PASS 的 sink 必须完成证据真实性抽检（`evidence_spotcheck_count >= 5`）
- [ ] REJECT 的 sink 有明确的修改要求
- [ ] 超过最大轮次的 sink 标记为 `⚠️待验证` 并保留证据缺口记录

## 输出路径

- `review/review_{sink_id}_{round}_{timestamp}.md`
- `review/index_{timestamp}.md`（批次总索引）
