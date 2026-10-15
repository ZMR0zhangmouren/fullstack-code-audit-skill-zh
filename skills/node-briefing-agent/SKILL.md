---
name: node-briefing-agent
description: Node.js 代码审计候选参数清单生成阶段 Skill。为每个 sink 生成不可跳过的参数检查清单（checklist），把"别漏参数"变成下游 Taint 与专项阶段必须逐项处理的输入。只负责列全参数，不判断安全性。
---

# Node.js 候选参数清单（Briefing）

## 目标

为每个 sink 生成**不可跳过的参数检查清单（checklist）**，把"别漏参数"变成下游 Taint 与漏洞专项阶段必须逐项处理的输入。

**Briefing 不判断参数是否安全，只负责列全。**

## 核心原则

- Briefing **只列参数，不判断安全**
- 每个参数必须标注：来源、进入 sink 的位置、后续需要验证的 barrier
- 这份 checklist 是漏洞专项的输入，遗漏参数 = 下游无法验证

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认遵循 `shared/AUDIT_EXECUTION_COMMON.md` 与 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（栈无关）

## 输入

- `node/scan_audit/scan_{filename|module}_{timestamp}.md`：Scan 阶段输出的 risks（含 taint_candidates）
- `node/route_mapping/params_{timestamp}.md`：路由参数映射（如存在）
- `node/route_mapping/middleware_inventory_{timestamp}.md`：中间件清单（确认 body parser / 静态目录等入口前置）
- `node_source_path`：Node.js 项目源码路径

## 输出 Schema

### node/briefing/briefing_{sink_id}_{timestamp}.md

每个 sink 必须生成一个独立的 checklist：

## 候选参数清单

| 候选参数 | 参数来源 | 进入 Sink 的位置 | 参数类型 | 后续检查（专项阶段必须验证） |
|---------|---------|-----------------|---------|---------------------------|
| `req.query.column` | Query 参数 | SQL 标识符位置（knex.raw 拼接） | 结构位置 | 服务端字段白名单 |
| `req.body.filter` | Body 对象 | `collection.find(req.body.filter)` 对象直通 | 查询对象 | Schema 校验 / 操作符过滤 |
| `req.body.config` | Body 对象 | `lodash.merge(defaults, req.body.config)` 合并目标 | 合并目标 | `__proto__` 键过滤与原型隔离 |
| `req.query.url` | Query 参数 | `axios.get(url)` URL 位 | URL | SSRF allowlist 与重定向策略 |
| `req.params.template` | Route 参数 | `ejs.render(template)` 模板表达式 | 模板表达式 | 模板来源固定化 |

### 参数来源分类

| 来源类型 | 说明 | 示例 |
|---------|------|------|
| `REQUEST` | 直接来自 HTTP 请求 | `req.query` / `req.params` / `req.body` / `req.headers` / `req.cookies` / 上传文件名 |
| `FRAMEWORK` | 框架注入的请求派生数据 | Next.js `getServerSideProps` 的 `params/query/req`、NestJS `@Param/@Body/@Query` 装饰器参数、tRPC input |
| `CONFIG` | 来自配置 | `.env`、`config/` 模块、`package.json`、默认值对象 |
| `STORAGE_READ` | 来自持久化存储读取 | 数据库查询结果、Redis 缓存、会话存储（注意：可能承载其他用户的输入 → 二次注入源） |
| `COMPUTED` | 代码计算生成 | 拼接、`Object.keys` 派生、路径解析中间值 |
| `CONSTANT` | 硬编码常量 | 字面量字符串、枚举值 |

### 进入 Sink 的位置分类

| 位置类型 | 说明 | 风险等级 |
|---------|------|---------|
| `VALUE_POSITION` | 值位置（WHERE 条件值、LIKE 值、比较值） | 中（取决于 barrier） |
| `STRUCTURE_POSITION` | 结构位置（查询字段名、排序键、对象键、表/集合名） | 高（通常无 barrier） |
| `QUERY_OBJECT` | 整个对象直通查询/合并（find(对象)、merge(对象)） | 高（NoSQL 操作符 / 原型链污染） |
| `MERGE_TARGET` | 递归合并目标（原型链污染面） | 高 |
| `DIRECT_SQL_TEXT` | 直接进入 SQL 文本 | 高 |
| `COMMAND_ARGUMENT` | 命令字符串或参数位 | 高 |
| `FILE_PATH` | 文件路径（读取/写入/解压） | 高 |
| `URL` | URL / URI / 代理转发目标 | 高 |
| `TEMPLATE_EXPRESSION` | 模板表达式 / 渲染字符串 | 高 |
| `EVAL_STRING` | eval / Function / vm 执行字符串 | 高 |
| `HEADER_VALUE` | Header 值 / Set-Cookie（CRLF 面） | 中 |
| `REDIRECT_TARGET` | 重定向目标 | 中 |

## 与下游专项阶段的衔接

```
Briefing 输出 checklist
    → 专项阶段逐项验证 checklist 中的每个参数
    → 对 STRUCTURE_POSITION / QUERY_OBJECT / MERGE_TARGET 参数优先验证
    → 对 VALUE_POSITION 参数验证 barrier 实际行为
    → 验证完成后输出命中结论与 EVID 证据
```

## 反模式（禁止）

- ❌ **在 Briefing 阶段排除参数**：如"`category_id` 已被 `parseInt` 处理，所以不列入 checklist"
- ❌ **遗漏参数**：如只列出 2 个参数，但 sink 中实际有 6 个动态参数
- ❌ **参数来源模糊**：如写"来自请求"而不具体说明是 `req.query` / `req.body` / `req.headers`
- ❌ **不标注进入位置**：如只写参数名，不说明是值位置还是结构位置 / 查询对象 / 合并目标

## 质量门禁

- [ ] 每个 sink 都有独立的 briefing_{sink_id}_{timestamp}.md
- [ ] checklist 列出 sink 中所有动态参数，无遗漏
- [ ] 每个参数都有明确的来源、位置和后续检查项
- [ ] 没有过早排除任何参数
- [ ] checklist 按参数类型分组（STRUCTURE_POSITION / QUERY_OBJECT / MERGE_TARGET 优先）

## 输出路径

- `node/briefing/briefing_{sink_id}_{timestamp}.md`（每个 sink 一个）
- `node/briefing/index_{timestamp}.md`（批次总索引）
