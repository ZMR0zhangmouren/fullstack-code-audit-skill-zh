---
name: dotnet-scan-audit
description: .NET 代码安全扫描阶段 Skill。负责识别文件中所有可疑 sink 点，同时标记已检查的安全区域，输出 risks + safe_regions 供下游 Coverage 阶段计算未覆盖 gap。只负责发现，不判断风险是否成立。
---

# .NET 安全扫描（Scan）

## 目标

对每个源文件进行风险发现扫描，**只负责发现可疑 sink 点，不判断风险是否成立**。

核心产出：
- `risks`：文件中所有可疑 sink 点及其参与的动态参数
- `safe_regions`：已检查但暂时无风险的代码区域

## 核心原则

**Scan 只负责发现，不负责验证。**

- 看到 sink 时，**不要急于判断是否有注入**
- 只需列出所有参与 sink 的动态参数名
- 把"是否安全"的判断留给下游 Taint 阶段
- 必须同时输出 `risks` 和 `safe_regions`，否则 Coverage 无法计算 gap

## 共享抓手索引引用

- 默认以 `shared/DOTNET_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/DOTNET_SINK_REFERENCE.md` 作为 Sink 类型定义参考
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）

## 输入

- `source_path`：.NET 项目源码路径
- `target_file`：当前扫描的单个源文件路径
- `timestamp`：生成时间戳

## 输出 Schema

输出到 `scan_audit/` 目录：

### 1. scan_audit/scan_{filename}_{timestamp}.md

每个被扫描的文件必须输出一个结构化扫描报告。

#### risks 部分

每个 sink 必须包含：

| 字段 | 说明 | 必填 |
|------|------|------|
| `sink_type` | 风险类型：`SQL_INJECTION` / `CMD_INJECTION` / `SSRF` / `XSS` / `FILE_READ` / `FILE_WRITE` / `DESER` / `XXE` / `SSTI` / `LDAP_INJECTION` / `EXPR_INJECTION` / `XPATH_INJECTION` / `NOSQL_INJECTION` / `AUTH_BYPASS` / `CSRF` / `OPEN_REDIRECT` / `CRLF_INJECTION` / `SECOND_ORDER` / `OTHER` | 是 |
| `line_range` | 代码行号范围，如 `45-52` | 是 |
| `dangerous_call` | 危险调用代码片段（原样摘录，不超过 5 行） | 是 |
| `taint_candidates` | 参与 sink 的所有动态参数名列表（**只列名字，不判断安全性**） | 是 |
| `audit_focus` | 后续需要验证的方向提示 | 是 |
| `is_structure_position` | 是否有参数进入 SQL/命令/模板等的结构位置（列名、表名、ORDER BY 等） | 建议 |

#### safe_regions 部分

每个已检查区域必须包含：

| 字段 | 说明 | 必填 |
|------|------|------|
| `line_range` | 代码行号范围 | 是 |
| `reason` | 为什么暂时安全 | 是 |

`reason` 必须具体，不能写"安全"。推荐写法：
- `纯工具函数，无外部输入`（如 `DateTime.Now.ToString()`）
- `常量硬编码，无动态参数`（如 `"SELECT * FROM users"`）
- `已确认参数化查询，动态参数已绑定`（需注明参数绑定方式）
- `字符串字面量拼接，无用户输入参与`

### 2. scan_audit/index_{timestamp}.md

扫描批次总索引，包含：
- 本次扫描的文件总数
- 发现 risks 的文件数
- 无发现（仅 safe_regions）的文件数
- 扫描失败的文件列表

## 扫描范围

必须覆盖以下文件类型：
- `*.cs`：C# 源文件
- `*.cshtml`：Razor 视图
- `*.razor`：Blazor 组件
- `*.config` / `*.json`：配置文件（检查危险开关）
- `*.vb`：VB.NET（如有）

排除目录：`bin/`, `obj/`, `.vs/`, `publish/`, `test/` 快照与缓存目录。

## 常见 Sink 类型识别清单

扫描时必须检查以下常见 sink 模式（基于 `DOTNET_SINK_REFERENCE.md`）：
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）

### SQL 注入
- `SqlCommand`, `DbCommand`, `ExecuteReader`, `ExecuteScalar`, `ExecuteNonQuery`
- `FromSqlRaw`, `ExecuteSqlRaw`, `SqlQueryRaw`
- `Dapper` 的 `Query` / `Execute`（当参数为非参数化时）
- 字符串拼接构建 SQL：`+` 拼接、`$"..."` 插值、`StringBuilder.Append`

### 命令注入
- `Process.Start`, `Process.StartInfo`
- `cmd.exe`, `powershell.exe` 参数拼接
- `ShellExecute`, `CreateProcess`

### SSRF
- `HttpClient.GetAsync`, `WebRequest.Create`, `HttpWebRequest`
- `Uri` 构造拼接用户输入

### 文件操作
- `File.ReadAllText`, `File.OpenRead`, `FileStream` 路径可控
- `File.WriteAllText`, `FileStream` 写入路径可控
- `IFormFile.SaveAs`, `IFormFile.CopyTo`
- `ZipArchive.ExtractToDirectory`

### 反序列化
- `BinaryFormatter.Deserialize`
- `JsonConvert.DeserializeObject`（`TypeNameHandling` 不为 None 时）
- `DataContractSerializer.ReadObject`
- `JavaScriptSerializer.Deserialize`

### XSS
- `@Html.Raw`, `MarkupString`
- `Response.Write`, `HttpResponse.Write`
- 模板渲染时用户输入直接输出

### XXE
- `XmlDocument.Load`, `XmlReader.Create`
- `XDocument.Parse`

### 模板注入 / SSTI
- `Razor.Parse`, `Engine.Razor.RunCompile`
- `Scriban.Template.Parse`, `FluidTemplate.Parse`

### 表达式注入
- `CSharpScript.EvaluateAsync`
- `DataTable.Compute`
- `NCalc.Evaluate`
- `Dynamic LINQ`

### LDAP 注入
- `DirectorySearcher.Filter`
- `LdapConnection.SendRequest`

### XPath 注入
- `XmlNode.SelectNodes`, `XPathNavigator.Select`

### NoSQL 注入
- `IMongoCollection.Find` 的 `BsonDocument` 可控
- `FilterDefinition` 构造拼接

## 反模式（禁止）

- ❌ **在 Scan 阶段判断参数是否安全**：如看到 `escape_like_literal()` 就标记为安全——这是 Taint 阶段的职责
- ❌ **只输出 risks，不输出 safe_regions**：Coverage 无法计算未覆盖 gap
- ❌ **遗漏安全区域的标记**：文件中无风险的区域也需要标记，否则 Coverage 会要求补检
- ❌ **safe_regions 理由模糊**：不能写"安全"，必须写具体理由

## 与下游阶段的衔接

```
Scan 输出 (risks + safe_regions)
    → Coverage 阶段计算未覆盖 gap
    → 大 gap 送回 Scan 补检
    → 补检后更新 risks / safe_regions
    → 最终 Scan 产物交给 Briefing 阶段生成候选参数清单
```

## 质量门禁

- [ ] 每个扫描的文件都有 scan_{filename}_{timestamp}.md 输出
- [ ] 每个文件都包含 risks 和 safe_regions（两者之一可为空，但字段必须存在）
- [ ] safe_regions 的理由具体、可验证
- [ ] taint_candidates 列出所有参与 sink 的动态参数，不遗漏
- [ ] 没有过早判断安全性的结论

## 输出路径

- `scan_audit/scan_{filename}_{timestamp}.md`（每个文件一个）
- `scan_audit/index_{timestamp}.md`（批次总索引）
