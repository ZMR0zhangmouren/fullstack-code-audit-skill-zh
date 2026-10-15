---
name: node-scan-audit
description: Node.js 代码安全扫描阶段 Skill。负责识别文件中所有可疑 sink 点，同时标记已检查的安全区域，输出 risks + safe_regions 供下游 Coverage 阶段计算未覆盖 gap。只负责发现，不判断风险是否成立。
---

# Node.js 安全扫描（Scan）

## 目标

对每个源文件进行风险发现扫描，**只负责发现可疑 sink 点，不判断风险是否成立**。

核心产出：
- `risks`：文件中所有可疑 sink 点及其参与的动态参数
- `safe_regions`：已检查但暂时无风险的代码区域

## 核心原则

**Scan 只负责发现，不负责验证。**

- 看到 sink 时，**不要急于判断是否有注入**
- 只需列出所有参与 sink 的动态参数名
- 把"是否安全"的判断留给下游 Taint / 专项阶段
- 必须同时输出 `risks` 和 `safe_regions`，否则 Coverage 无法计算 gap

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为 Sink 类型定义参考
- 默认遵循 `shared/AUDIT_EXECUTION_COMMON.md` 与 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（栈无关）

## 输入

- `node_source_path`：Node.js 项目源码路径
- `target_file`：当前扫描的单个源文件路径
- `timestamp`：生成时间戳

## 输出 Schema

输出到 `node/scan_audit/` 目录：

### 1. node/scan_audit/scan_{filename|module}_{timestamp}.md

每个被扫描的文件必须输出一个结构化扫描报告。

#### risks 部分

每个 sink 必须包含：

| 字段 | 说明 | 必填 |
|------|------|------|
| `sink_type` | 风险类型：`CMD_INJECTION` / `EVAL_EXEC` / `SSRF` / `XSS` / `SSTI` / `FILE_READ` / `FILE_WRITE` / `FILE_UPLOAD` / `ARCHIVE_EXTRACT` / `DESER` / `XXE` / `SQL_INJECTION` / `NOSQL_INJECTION` / `LDAP_INJECTION` / `EXPR_INJECTION` / `XPATH_INJECTION` / `PROTO_POLLUTION` / `AUTH_BYPASS` / `CSRF` / `OPEN_REDIRECT` / `CRLF_INJECTION` / `SECOND_ORDER` / `OTHER` | 是 |
| `line_range` | 代码行号范围，如 `45-52` | 是 |
| `dangerous_call` | 危险调用代码片段（原样摘录，不超过 5 行） | 是 |
| `taint_candidates` | 参与 sink 的所有动态参数名列表（**只列名字，不判断安全性**） | 是 |
| `audit_focus` | 后续需要验证的方向提示 | 是 |
| `is_structure_position` | 是否有参数进入对象键 / 查询字段名 / 模板表达式等结构位置 | 建议 |

#### safe_regions 部分

每个已检查区域必须包含：

| 字段 | 说明 | 必填 |
|------|------|------|
| `line_range` | 代码行号范围 | 是 |
| `reason` | 为什么暂时安全 | 是 |

`reason` 必须具体，不能写"安全"。推荐写法：
- `纯工具函数，无外部输入`（如 `dayjs(ts).format()`）
- `常量硬编码，无动态参数`（如 `db.query('SELECT * FROM users')` 固定字符串）
- `已使用参数化/占位符查询，动态参数已绑定`（需注明驱动与绑定方式）
- `对象键来自固定枚举，无用户输入参与`

### 2. node/scan_audit/index_{timestamp}.md

扫描批次总索引，包含：
- 本次扫描的文件总数
- 发现 risks 的文件数
- 无发现（仅 safe_regions）的文件数
- 扫描失败的文件列表

## 扫描范围

必须覆盖以下文件类型：
- `*.js` / `*.mjs` / `*.cjs`：JavaScript 源文件（含 CommonJS 与 ESM）
- `*.ts` / `*.tsx` / `*.jsx`：TypeScript / JSX 源文件
- `package.json`：`scripts`（postinstall/preinstall 生命周期钩子）、`dependencies` 异常来源
- `.env*` / `*.config.js` / `*.config.ts`：配置文件（危险开关、密钥硬编码）

排除目录：`node_modules/`, `dist/`, `build/`, `coverage/`, `.next/`, `.nuxt/`, `vendor/`。

## 常见 Sink 类型识别清单

扫描时必须检查以下常见 sink 模式（基于 `NODE_SINK_REFERENCE.md`）：

### 命令注入
- `child_process.exec`, `execSync`, `spawn(shell:true)`, `execFile`
- `node:child_process` 别名导入后的同族调用

### 代码/表达式执行
- `eval(`, `new Function(`, `vm.runInNewContext`, `vm.runInThisContext`
- `require(动态字符串)`, `import(动态字符串)`
- `expr-eval`, `mathjs.evaluate`, `jexl`, `jsonata` 等表达式引擎求值点

### SSRF
- `axios(`, `axios.get/post`, `fetch(`, `got(`, `request(`, `undici`, `http.get`, `https.get`
- URL 由拼接或用户输入构造；`followRedirects` / `maxRedirects` 配置

### 文件操作
- `fs.readFile`, `fs.readFileSync`, `fs.createReadStream` 路径可控
- `fs.writeFile`, `fs.writeFileSync`, `fs.appendFile` 写入路径可控
- `multer` / `busboy` / `formidable` 上传落地路径
- `unzipper`, `adm-zip`, `yauzl`, `tar-stream` 解压路径（Zip Slip）

### 反序列化 / 对象注入
- `yaml.load`（js-yaml <4 且未设 `schema`）、`js-yaml.load(unsafe)`
- `node-serialize.unserialize`, `serialize-javascript` 反序列化方向, `funcster`
- `Object.assign`, `lodash.merge/set/defaultsDeep`, `deepmerge`, `@zurawiki/deep-copy` 递归合并目标可控

### SQL / NoSQL 注入
- 字符串拼接构建 SQL：`+` 拼接、模板字符串 `` `${var}` `` 插值
- `mysql` / `mysql2` 的 `query(拼接)` 而非 `execute(占位符)`
- `knex.raw`, `sequelize.literal`, `prisma.$queryRawUnsafe`
- `mongodb` 的 `collection.find(对象直通)`, `$where`, `$regex` 可控

### XSS / SSTI
- `res.send(用户输入)`, `innerHTML =`, `dangerouslySetInnerHTML`
- `ejs.render(用户输入)`, `pug.render(用户输入)`, `Handlebars.compile(用户输入)`, `nunjucks.renderString`

### XXE / XPath / LDAP
- `xml2js`, `sax`, `fast-xml-parser`, `libxmljs` 解析不可信 XML
- `xpath.select(拼接)`
- `ldapjs` 的 `search({filter: 拼接})`

### 开放重定向 / CRLF
- `res.redirect(用户输入)`, `location = 用户输入`
- `res.setHeader(/res.append(/res.writeHead(` 值含 `\r\n`

## 反模式（禁止）

- ❌ **在 Scan 阶段判断参数是否安全**：如看到 `escapeHtml()` 就标记为安全——这是专项阶段的职责
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

- [ ] 每个扫描的文件都有 scan_{filename|module}_{timestamp}.md 输出
- [ ] 每个文件都包含 risks 和 safe_regions（两者之一可为空，但字段必须存在）
- [ ] safe_regions 的理由具体、可验证
- [ ] taint_candidates 列出所有参与 sink 的动态参数，不遗漏
- [ ] 没有过早判断安全性的结论

## 输出路径

- `node/scan_audit/scan_{filename|module}_{timestamp}.md`（每个文件/模块一个）
- `node/scan_audit/index_{timestamp}.md`（批次总索引）
