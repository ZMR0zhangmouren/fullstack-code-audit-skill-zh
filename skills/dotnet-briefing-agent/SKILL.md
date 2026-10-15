---
name: dotnet-briefing-agent
description: .NET 代码审计候选参数清单生成阶段 Skill。为每个 sink 生成不可跳过的参数检查清单（checklist），把"别漏参数"变成下游 Taint 阶段必须逐项处理的输入。只负责列全参数，不判断安全性。
---

# .NET 候选参数清单（Briefing）

## 目标

为每个 sink 生成**不可跳过的参数检查清单（checklist）**，把"别漏参数"变成下游 Taint 阶段必须逐项处理的输入。

**Briefing 不判断参数是否安全，只负责列全。**

## 核心原则

- Briefing **只列参数，不判断安全**
- 每个参数必须标注：来源、进入 sink 的位置、后续需要验证的 barrier
- 这份 checklist 是 Taint 的输入，遗漏参数 = 下游无法验证

## 输入

- `scan_audit/scan_{filename}_{timestamp}.md`：Scan 阶段输出的 risks（含 taint_candidates）
- `route_mapping/params_{timestamp}.md`：路由参数映射（如存在）
- `source_path`：项目源码路径

## 输出 Schema

### briefing_{sink_id}_{timestamp}.md

每个 sink 必须生成一个独立的 checklist：

## 候选参数清单

| 候选参数 | 参数来源 | 进入 Sink 的位置 | 参数类型 | 后续检查（Taint 阶段必须验证） |
|---------|---------|-----------------|---------|---------------------------|
| `column["column_key"]` | 配置表读取 | SQL 列标识符位置 | 结构位置 | 服务端字段白名单 |
| `keyword` | 请求 Query 参数 | LIKE 值位置 | 值位置 | `escape_like_literal()` 实际实现 |
| `category_id` | 请求 Route 参数 | WHERE 等值条件 | 值位置 | `strict_int()` 实际实现 |
| `sort_key` | 请求 Query 参数 | ORDER BY 子句 | 结构位置 | 服务端白名单映射 |
| `limit` | 请求 Query 参数 | LIMIT 子句 | 值位置 | `strict_int()` 实际实现 |
| `offset` | 请求 Query 参数 | OFFSET 子句 | 值位置 | `strict_int()` 实际实现 |

### 参数来源分类

| 来源类型 | 说明 | 示例 |
|---------|------|------|
| `REQUEST` | 直接来自 HTTP 请求 | Query, Route, Body, Header, Cookie, Form |
| `CONFIG` | 来自配置文件/配置表 | appsettings.json, 数据库配置表 |
| `STORAGE_READ` | 来自持久化存储读取 | 数据库查询结果、缓存读取、Session 读取 |
| `COMPUTED` | 代码计算生成 | 拼接、转换、派生字段 |
| `CONSTANT` | 硬编码常量 | 字面量字符串、枚举值 |

### 进入 Sink 的位置分类

| 位置类型 | 说明 | 风险等级 |
|---------|------|---------|
| `VALUE_POSITION` | 值位置（如 WHERE 条件值、LIKE 值） | 中（取决于 barrier） |
| `STRUCTURE_POSITION` | 结构位置（如列名、表名、ORDER BY） | 高（通常无 barrier） |
| `DIRECT_SQL_TEXT` | 直接进入 SQL 文本 | 高 |
| `COMMAND_ARGUMENT` | 命令参数 | 高 |
| `FILE_PATH` | 文件路径 | 高 |
| `URL` | URL / URI | 高 |
| `TEMPLATE_EXPRESSION` | 模板表达式 | 高 |

## 与下游 Taint 阶段的衔接

```
Briefing 输出 checklist
    → Taint 阶段逐项验证 checklist 中的每个参数
    → 对 STRUCTURE_POSITION 参数优先验证
    → 对 VALUE_POSITION 参数验证 barrier 实际行为
    → 验证完成后输出 taint_nodes
```

## 反模式（禁止）

- ❌ **在 Briefing 阶段排除参数**：如"category_id 已被 strict_int 处理，所以不列入 checklist"
- ❌ **遗漏参数**：如只列出 2 个参数，但 sink 中实际有 6 个动态参数
- ❌ **参数来源模糊**：如写"来自请求"而不具体说明是 Query/Body/Header
- ❌ **不标注进入位置**：如只写参数名，不说明是值位置还是结构位置

## 质量门禁

- [ ] 每个 sink 都有独立的 briefing_{sink_id}_{timestamp}.md
- [ ] checklist 列出 sink 中所有动态参数，无遗漏
- [ ] 每个参数都有明确的来源、位置和后续检查项
- [ ] 没有过早排除任何参数
- [ ] checklist 按参数类型分组（STRUCTURE_POSITION 优先）

## 输出路径

- `briefing/briefing_{sink_id}_{timestamp}.md`（每个 sink 一个）
- `briefing/index_{timestamp}.md`（批次总索引）
