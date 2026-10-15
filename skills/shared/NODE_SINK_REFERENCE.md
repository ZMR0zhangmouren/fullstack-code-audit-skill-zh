# Node.js Sink 参考（供 node-route-tracer 与各漏洞专项统一对齐）

本文件是 Node.js 全栈扩展的 Sink 判定基准。Sink 分类代码与 SEVERITY 类型代码保持一致：
`SQL / NOSQL / CMD / SSRF / XSS / DOMXSS / SSTI/TPL / FILE / WRITE / UPLOAD / ARCHIVE / REDIR / DESER / EXPR / PROTO / REDOS / SESS / CRYPTO / CSRF / CFG`。

每个类型章节给出：
- **Sink API 清单（含包名）**：Node.js 原生或 npm 生态中真实存在的高危调用点；
- **可控参数位**：第几个参数、options 对象中的哪个字段，或链式调用中的哪个入参最常被外部输入污染；
- **参考 Barrier**：缓解/检测时应重点核对的校验、隔离或配置手段。

> 说明：同一 API 既可能是 Sink，也可能是合法调用；是否构成漏洞取决于“外部可控输入是否未经验证进入危险参数位”。

---

## SQL

### 原生驱动

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `connection.query(sql, callback)` | `mysql` / `mysql2` | 第 1 参数 `sql` | 占位符 `?` + 参数数组；禁止字符串拼接 |
| `connection.query(options, callback)` | `mysql` / `mysql2` | `options.sql` | 同上 |
| `connection.execute(sql, values, callback)` | `mysql2` | 第 1 参数 `sql` | prepared statement + 参数化 values |
| `client.query(text, values, callback)` | `pg` | 第 1 参数 `text` | `$1, $2` 占位符 + values 数组 |
| `pool.query(text, values)` | `pg` | 第 1 参数 `text` | 同上 |

### ORM / Query Builder

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `knex.raw(sql, bindings)` | `knex` | 第 1 参数 `sql` | 占位符 `?` / `:key:` + bindings |
| `sequelize.query(sql, options)` | `sequelize` | `options.replacements` / `options.bind` 之外直接拼接的 `sql` | `replacements` / `bind` 参数化；`type: QueryTypes.SELECT` 只读化 |
| `Model.findAll({ where: sequelize.literal(userInput) })` | `sequelize` | `sequelize.literal` 入参 | 避免用户输入进入 `literal`；字段白名单 |
| `repository.query(rawSql)` | `typeorm` | 第 1 参数 | 参数化查询；`Repository.query(sql, params)` |
| `getManager().query(rawSql)` | `typeorm` | 第 1 参数 | 同上 |

### 动态片段（无法参数化，需白名单）

- `ORDER BY ${userColumn}` — 列名/别名位
- `LIMIT / OFFSET ${userNumber}` — 数值位（需强转整数并范围校验）
- `FROM ${userTable}` — 表名位
- `WHERE ${dynamicFragment}` — 条件片段位

---

## NOSQL

### MongoDB / Mongoose

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `collection.find(query)` | `mongodb` | `query` 对象整体 | 校验对象键白名单；禁用 `$where` |
| `collection.findOne(query)` | `mongodb` | `query` 对象 | 同上 |
| `Model.find(query)` | `mongoose` | `query` 对象 | 同上；使用 `mongoose` schema 静态类型 |
| `Model.findOne(query)` | `mongoose` | `query` 对象 | 同上 |
| `Model.find({ $where: userInput })` | `mongoose` | `$where` 字段 | 禁止 `$where`；`mongoose.set('sanitizeFilter', true)` |
| `Model.find({ field: { $regex: userInput } })` | `mongoose` | `$regex` 字段 | 正则白名单 / `RegExp.escape` |
| `Model.where().$where(userInput)` | `mongoose` | `$where` 入参 | 禁止 |

### Redis

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `redisClient.eval(script, ...)` | `redis` / `ioredis` | 第 1 参数 Lua `script` | 避免脚本拼接；使用 EVALSHA + 预注册脚本 |
| `redisClient.sendCommand(command)` | `redis` / `ioredis` | `command` 数组元素 | 命令白名单；键名转义 |

### Elasticsearch

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `client.search({ body: userObject })` | `@elastic/elasticsearch` | `body.query` 对象 | 查询 DSL 白名单；避免直接拼接 JSON |

---

## CMD

### child_process

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `exec(command, callback)` | `child_process` | 第 1 参数 `command` | 数组化参数：`execFile` / `spawn`；避免 shell 解释 |
| `execSync(command)` | `child_process` | 第 1 参数 `command` | 同上 |
| `execFile(file, args, options)` | `child_process` | `args` 数组元素 | 不设置 `options.shell = true`；参数数组化 |
| `spawn(command, args, options)` | `child_process` | 当 `options.shell = true` 时第 1 参数 | 默认 `shell: false`；参数数组化 |
| `fork(modulePath, args)` | `child_process` | `args` 数组元素 | 校验参数内容 |

### 间接命令执行

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `shelljs.exec(cmd)` | `shelljs` | 第 1 参数 `cmd` | 禁止用户输入进入命令字符串 |
| `node-cmd.run(cmd)` | `node-cmd` | 第 1 参数 `cmd` | 同上 |

---

## SSRF

### HTTP 客户端

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `axios.get(url, config)` | `axios` | 第 1 参数 `url`；`config.baseURL` + `config.url` 拼接 | URL 白名单/主机名白名单；禁用 `maxRedirects` 或限制协议 |
| `axios.request(config)` | `axios` | `config.url` / `config.baseURL` | 同上 |
| `fetch(url, init)` | 原生 `fetch` / `node-fetch` | 第 1 参数 `url` | 协议白名单（http/https）；主机白名单 |
| `got(url, options)` | `got` | 第 1 参数 `url` | 同上 |
| `request(url, options)` | `request` / `postman-request` | 第 1 参数 `url` | 同上 |
| `http.get(url, callback)` | 原生 `http` / `https` | 第 1 参数 `url` | 同上 |
| `undici.request(url, options)` | `undici` | 第 1 参数 `url` | 同上 |
| `urllib.request(url, options)` | `urllib` | 第 1 参数 `url` | 同上 |

### 特殊场景

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| Webhook 回调 URL | 业务代码 | 用户提供的 URL 字符串 | URL 协议/主机白名单；禁用 file:// / gopher:// / dict:// |
| PDF 生成 URL（puppeteer / html-pdf） | `puppeteer` / `html-pdf` | 渲染目标 URL | 禁止访问内网/元数据地址；URL 白名单 |
| 图片下载 URL | `sharp` / `jimp` / `axios` | URL 字符串 | 白名单 + 响应 Content-Type 校验 |

---

## XSS

### 服务端输出

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `res.send(markup)` | Express 原生 | 第 1 参数（当 Content-Type 为 text/html 时） | 输出 HTML 编码；使用模板引擎自动转义 |
| `res.render(view, locals)` | Express 原生 | `locals` 中未编码的字段 | 模板引擎默认转义；禁用 `{{{ }}}` / `<%-` 等原样输出 |
| `ejs.render(template, data)` | `ejs` | `template` 或 `data` 字段 | `<%= %>` 自动编码；避免 `<%- userInput %>` |
| `pug.render(template, data)` | `pug` | `data` 进入 `!=` 点位 | 避免 `!=` 输出用户数据 |
| `nunjucks.renderString(template, context)` | `nunjucks` | `template` / `context` | 默认转义；关闭 `autoescape` 危险 |
| `handlebars.compile(template)(context)` | `handlebars` | `template` / `context` | 默认 HTML 编码；使用 `{{{ }}}` 需显式审批 |
| `mustache.render(template, view)` | `mustache` | `template` / `view` | 默认转义；注意 tripleMustache |

### 编码/转义配置

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `xss(userInput, options)` | `xss` | 第 1 参数；`options.whiteList` | 配置严格白名单；禁止 `style` / `on*` 事件 |
| `DOMPurify.sanitize(dirty)` | `dompurify` | 第 1 参数 | 服务端/客户端均配置 `FORBID_ATTR` / `FORBID_TAGS` |

---

## DOMXSS

### 客户端 DOM 操作

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `document.write(userInput)` | 浏览器原生 | 第 1 参数 | 避免将 location.hash / search 直接写入 |
| `element.innerHTML = userInput` | 浏览器原生 | 右侧赋值 | 使用 `textContent` / `innerText` 替代；DOMPurify 先清洗 |
| `element.outerHTML = userInput` | 浏览器原生 | 右侧赋值 | 同上 |
| `document.createRange().createContextualFragment(html)` | 浏览器原生 | `html` 参数 | 先清洗 |
| `jQuery.html(userInput)` | `jquery` | 第 1 参数 | 使用 `.text()` 替代；配置 `DOMPurify` |
| `jQuery.append(userInput)` | `jquery` | 第 1 参数 | 同上 |
| `React dangerouslySetInnerHTML={{ __html: userInput }}` | React 原生 | `__html` 字段 | 必须先行清洗；禁止直接放入未处理的外部 HTML |
| `Vue v-html="userInput"` | Vue 原生 | `v-html` 表达式 | 同上 |

### JavaScript 执行型 Sink

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `eval(userInput)` | 浏览器/Node 原生 | 第 1 参数 | 禁止任何外部输入进入 |
| `new Function(userInput)` | 浏览器/Node 原生 | 第 1 参数 | 禁止 |
| `setTimeout(userCode, delay)` | 浏览器/Node 原生 | 第 1 参数为字符串时 | 仅传入函数 |
| `setInterval(userCode, delay)` | 浏览器/Node 原生 | 第 1 参数为字符串时 | 仅传入函数 |
| `window.location = userUrl` | 浏览器原生 | 右侧赋值 | URL 白名单；避免 `javascript:` 伪协议 |

---

## SSTI/TPL

### 服务端模板引擎

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `ejs.render(userTemplate, data)` | `ejs` | `userTemplate` | 禁止用户控制模板字符串；模板文件白名单 |
| `pug.compile(userTemplate)` | `pug` | `userTemplate` | 同上 |
| `nunjucks.renderString(userTemplate, context)` | `nunjucks` | `userTemplate` | 同上 |
| `handlebars.compile(userTemplate)` | `handlebars` | `userTemplate` | 同上；限制 helper 注册 |
| `mustache.render(userTemplate, view)` | `mustache` | `userTemplate` | 同上 |
| `res.render(view, locals)` | Express 原生 | `view` 名称 | 视图名白名单；禁止用户控制模板路径 |

### 模板表达式求值

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `lodash.template(userTemplate)(data)` | `lodash` | `userTemplate` | 禁止用户输入控制模板 |
| `dot.template(userTemplate)` | `dot`（npm 包名；仓库 olado/doT） | `userTemplate` | 同上 |
| `eta.render(userTemplate, data)` | `eta` | `userTemplate` | 同上 |

---

## FILE/WRITE

### 文件读取

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `fs.readFile(path, callback)` | 原生 `fs` | 第 1 参数 `path` | 路径规范化 + 前缀白名单；禁止 `..` / 空字节 |
| `fs.readFileSync(path)` | 原生 `fs` | 第 1 参数 `path` | 同上 |
| `fs.createReadStream(path)` | 原生 `fs` | 第 1 参数 `path` | 同上 |
| `fs.open(path, flags, callback)` | 原生 `fs` | 第 1 参数 `path` | 同上 |
| `res.sendFile(path, options)` | Express 原生 | 第 1 参数 `path` | `root` 选项限定根目录；路径规范化 |
| `path.join(base, userPath)` | 原生 `path` | 第 2 参数起 | 先校验 base；规范化后检查前缀 |
| `path.resolve(userPath)` | 原生 `path` | 第 1 参数起 | 与根目录对比；避免相对路径逃逸 |

### 路径穿越模式

- `../` / `..\` 目录遍历
- URL 编码 `%2e%2e%2f`
- 空字节 `%00`（旧版 Node / 底层 C 库）
- 软链接/硬链接指向敏感文件

### 文件写入

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `fs.writeFile(path, data, callback)` | 原生 `fs` | 第 1 参数 `path`；第 2 参数 `data` | 路径前缀白名单；禁止用户控制扩展名落盘 Web 目录 |
| `fs.writeFileSync(path, data)` | 原生 `fs` | 第 1 / 2 参数 | 同上 |
| `fs.appendFile(path, data, callback)` | 原生 `fs` | 第 1 / 2 参数 | 同上；防止日志注入 |
| `fs.createWriteStream(path)` | 原生 `fs` | 第 1 参数 `path` | 同上 |
| `fs.open(path, 'w', callback)` | 原生 `fs` | 第 1 参数 `path` | 同上 |

### 危险模式

- 用户控制文件名 + 写入 `public/` / `static/` 目录 → WebShell
- 用户控制路径 + 写入配置文件目录 → 配置覆盖
- 用户控制日志路径 → 日志注入 + 路径穿越

---

## UPLOAD

### 上传接收

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `multer({ dest: folder })` | `multer` | `dest` / `filename` 回调；`fileFilter` | `fileFilter` 白名单扩展名 + MIME；重命名为随机名 |
| `multer({ storage: diskStorage({ destination, filename }) })` | `multer` | `destination` / `filename` 回调 | 限制落点目录；禁止原始文件名直接落盘 |
| `busboy.on('file', (name, file, info) => {})` | `busboy` | `info.filename` | 文件名白名单；限制落点 |
| `formidable({ uploadDir })` | `formidable` | `uploadDir`；`file.originalFilename` | 限制目录；重命名 |
| `req.files` / `req.file` | Express + `multer` | `file.originalname` / `file.mimetype` | 后端校验；不依赖客户端 MIME |

### 关键检查点

- 扩展名：白名单 > 黑名单；注意双扩展名 `.jpg.php`
- Content-Type：客户端可伪造，必须后端魔数/扩展名交叉校验
- 文件大小：`limits.fileSize`
- 落盘路径：禁止 Web 可访问目录执行文件
- 重命名策略：UUID / 哈希，保留原始名仅作展示且需清洗

---

## ARCHIVE

### 解压 API

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `extractZip(zipPath, { dir })` | `extract-zip` | `zipPath`；`dir` | 逐条目校验 `entry.fileName`；拒绝 `..` |
| `AdmZip.extractAllTo(targetPath, overwrite)` | `adm-zip` | `targetPath` | 校验条目名；限制落点目录 |
| `tar.extract({ file, cwd })` | `tar` | `file`；`cwd` | `strip` 参数；校验条目路径 |
| `yauzl.open(zipPath, options, callback)` | `yauzl` | `zipPath`；`entry.fileName` | 校验 `fileName`；符号链接审查 |
| `unzipper.Open.file(zipPath)` | `unzipper` | `zipPath`；`entry.path` | 同上 |

### Zip Slip 模式

- `entry.fileName` / `entry.path` 含 `../` → 写入目标目录外
- 符号链接条目 → 指向 `/etc/passwd` 等敏感文件
- 绝对路径条目 → 覆盖系统文件

---

## REDIR

### Express / Connect

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `res.redirect(url)` | Express 原生 | 第 1 参数 `url` | URL allowlist；仅允许相对路径且校验路径前缀 |
| `res.redirect(status, url)` | Express 原生 | 第 2 参数 `url` | 同上 |
| `res.location(url)` | Express 原生 | 第 1 参数 `url` | 同上 |

### 认证/SSO 流程

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `passport.authenticate(..., { successRedirect: userUrl })` | `passport` | `successRedirect` / `failureRedirect` | 硬编码或白名单 |
| OAuth `redirect_uri` | `passport-oauth2` / 业务代码 | 回调 URL | 严格匹配预注册 redirect_uri |
| OIDC `post_logout_redirect_uri` | `openid-client` | 登出后跳转 URL | 白名单 |

### 常见参数名

- `returnUrl` / `return_url` / `redirect` / `redirectUrl` / `next` / `goto` / `continue` / `callback`

---

## DESER

### JSON / JS 原生

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `JSON.parse(userInput)` | 原生 | 第 1 参数 | 先 schema 校验；防止 `__proto__` 污染与 ReDoS 大 key |
| `eval(userInput)` | 原生 | 第 1 参数 | 完全禁止 |
| `new Function(userInput)` | 原生 | 第 1 参数 | 完全禁止 |

### 第三方序列化

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `serialize.unserialize(userInput)` | `node-serialize` | 第 1 参数 | 禁止处理不可信输入 |
| `serialize(obj)` 的输出被传入 `eval(serialized)` 或 `new Function('return ' + serialized)()` | `serialize-javascript` | 恢复执行的代码字符串 | 仅信任来源；避免函数/正则恢复 |
| `yaml.load(userInput)` | `js-yaml` | 第 1 参数 | 使用 `yaml.safeLoad` / `yaml.load` 关闭 `!!js/function` |
| `msgpack.decode(userInput)` | `msgpack-lite` / `msgpack` | 第 1 参数 | 类型白名单；避免 typeless 模式 |
| `bson.deserialize(userInput)` | `bson` | 第 1 参数 | 限制缓冲区大小；校验对象结构 |

### 原型链污染入口

- `JSON.parse` + 后续 `Object.assign({}, parsed)` 未清洗 `__proto__`
- `merge({}, userInput)`（见 PROTO 节）

---

## EXPR

### 动态执行

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `eval(expression)` | 原生 | 第 1 参数 | 禁止 |
| `new Function(expression)` | 原生 | 第 1 参数 | 禁止 |
| `vm.runInThisContext(code)` | 原生 `vm` | 第 1 参数 `code` | 禁止用户输入 |
| `vm.runInNewContext(code, sandbox)` | 原生 `vm` | 第 1 参数 `code` | 沙箱隔离但不能替代输入校验 |
| `vm.runInContext(code, context)` | 原生 `vm` | 第 1 参数 `code` | 同上 |
| `vm.Script(code).runInContext(ctx)` | 原生 `vm` | 构造函数 `code` | 同上 |

### 表达式求值库

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `Parser.parse(expr).evaluate(context)` | `expr-eval` / `mathjs` | 表达式字符串 | 表达式白名单；禁用危险函数 |
| `math.evaluate(expression)` | `mathjs` | 表达式字符串 | 限制函数集；使用 `math.parse` + 白名单 |
| `safeEval(expression)` | `safe-eval` / `notevil` | 表达式字符串 | 仍须校验来源与表达式范围 |

---

## PROTO

### 原型链污染高危 API

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `_.set(object, path, value)` | `lodash` | `path` 含 `__proto__.x` / `constructor.prototype.x` | 升级到无漏洞版本；路径白名单 |
| `_.merge(target, source)` | `lodash` | `source` 对象键 `__proto__` / `constructor` | 升级到 ≥4.17.21；使用 `lodash/fp` 不可变合并 |
| `_.defaultsDeep(object, sources)` | `lodash` | `sources` 中含污染对象 | 同上 |
| `_.assignIn(target, source)` | `lodash` | `source` 对象键 | 避免不可信 source 进入 |
| `Object.assign(target, source)` | 原生 | `source` 中含 `__proto__` / `constructor` | 先清洗 key；使用 `Object.create(null)` |
| `Object.defineProperty(target, key, descriptor)` | 原生 | `key` 为 `__proto__` | 校验 key；避免污染原型 |
| `merge(target, source)` | `deep-extend` / `extend` / `utils-merge` | `source` 对象 | 升级到安全版本；key 白名单 |
| `hoek.merge(target, source)` | `hoek` | `source` 对象 | 升级到安全版本 |
| `JSON.parse(userInput)` + 反序列化后遍历赋值 | 业务代码 | 用户输入的 JSON 键 | 清洗 `__proto__` / `constructor` / `prototype` |

### 污染检测 Barrier

- 输入 key 黑名单：`__proto__`、`constructor`、`prototype`
- 使用 `Object.create(null)` 或 `Map` 替代普通对象存储不可信 key
- 使用 `Object.freeze(Object.prototype)` 作为纵深防御

---

## REDOS

### 正则构造

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `new RegExp(userPattern, flags)` | 原生 | 第 1 参数 `pattern` | 禁止用户输入构造正则；必须时使用 ReDoS 检测 |
| `new RegExp(userPattern)` | 原生 | 第 1 参数 `pattern` | 同上 |
| `string.match(userRegex)` | 原生 | 正则对象或字符串 | 避免用户输入直接作为正则 |
| `string.search(userRegex)` | 原生 | 同上 | 同上 |
| `string.replace(userRegex, replacement)` | 原生 | 同上 | 同上 |
| `string.split(userRegex)` | 原生 | 同上 | 同上 |
| `validator.matches(input, pattern)` | `validator` | `pattern` 参数 | 仅使用内置白名单模式 |
| `validator.isEmail(input, options)` | `validator` | `options` 中的自定义 host_blacklist | 避免用户可控正则 |

### ReDoS 检测工具

- `recheck`（`makenowjust/recheck`）用于检测危险正则
- `safe-regex` 用于静态判定

---

## SESS

### Cookie / Session

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `res.cookie(name, value, options)` | Express 原生 | `options.httpOnly` / `options.secure` / `options.sameSite` / `options.maxAge` | 生产环境 `httpOnly=true`, `secure=true`, `sameSite=strict/lax` |
| `req.session.userId = userInput` | `express-session` | session 字段赋值 | 仅存储可信标识；避免存储敏感信息 |
| `req.session.destroy()` | `express-session` | 调用时机 | 登出/异常时销毁 |
| `cookieSession()` | `cookie-session` | 签名密钥 `keys` | 强密钥；`signed=true` |

### JWT

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `jwt.sign(payload, secretOrPrivateKey, options)` | `jsonwebtoken` | `options.algorithm` / 密钥来源 | 钉死 `algorithm`；HS256/RS256 显式指定 |
| `jwt.verify(token, secretOrPublicKey, options)` | `jsonwebtoken` | `options.algorithms` 白名单 | 显式 `algorithms: ['HS256']`；禁用 `none` |
| `jwt.decode(token, { complete: true })` | `jsonwebtoken` | 仅解码不验证，不可用于授权 | 必须与 `verify` 区分 |
| `new SignJWT(payload).setProtectedHeader(...).sign(key)` | `jose` | header alg | 钉死算法 |
| `jwtVerify(token, secret, options)` | `jose` | `options.algorithms` | 白名单 |

---

## CRYPTO

### 弱哈希/加密

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `crypto.createHash('md5')` | 原生 `crypto` | 算法名 | 使用 `sha256` / `sha512`；禁止 md5/sha1 用于安全场景 |
| `crypto.createHash('sha1')` | 原生 `crypto` | 算法名 | 同上 |
| `md5(userInput)` | `md5` / `crypto-js` | 算法名 | 同上 |
| `crypto.createCipher(algorithm, password)` | 原生 `crypto`（已弃用） | 算法名 | 使用 `createCipheriv` + 随机 IV |
| `crypto.createDecipher(algorithm, password)` | 原生 `crypto`（已弃用） | 算法名 | 同上 |

### 随机数/密钥

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `Math.random()` | 原生 | 返回值用于 token / 验证码 | 使用 `crypto.randomBytes` / `crypto.randomUUID` |
| `crypto.randomBytes(size)` | 原生 | 生成长度 | 用于 IV / nonce / token；长度足够 |
| `crypto.pbkdf2Sync(password, salt, iterations, keylen, digest)` | 原生 | `iterations` / `digest` | iterations ≥ 100k；使用 `sha512` |
| `crypto.scryptSync(password, salt, keylen)` | 原生 | 参数 | 推荐用于密码派生 |
| 硬编码密钥于 `process.env.SECRET` 之外 | 业务代码 | 密钥字符串 | 使用 KMS / Vault；禁止提交 |

---

## CSRF

### 防护机制缺失

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `app.use(csrf())` 未挂载 | `csurf` | 全局/路由级中间件 | 所有状态变更路由挂载 |
| `csurf({ cookie: { ... } })` | `csurf` | `cookie` 配置 | 优先使用 session 存储 token |
| `app.post('/action', handler)` 无 csrf 校验 | Express 原生 | 路由注册 | 配合 `csurf` + 模板注入 `req.csrfToken()` |
| `app.use(cors({ credentials: true, origin: '*' }))` | `cors` | `origin` 配置 | 关闭通配符 + credentials 组合 |

### 绕过场景

- Content-Type `text/plain` / `application/x-www-form-urlencoded` 不触发 CORS preflight
- 子域 Cookie 注入覆盖 csrf token
- SameSite=None 且未 Secure 导致跨站携带 Cookie

---

## CFG

### CORS

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `app.use(cors({ origin: '*' }))` | `cors` | `origin` | 显式 origin 白名单 |
| `cors({ credentials: true, origin: true })` | `cors` | `origin` 回调 | 禁止反射 origin + credentials |
| `res.setHeader('Access-Control-Allow-Origin', userOrigin)` | 原生 | 头值 | 白名单 |

### 安全头

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `app.use(helmet())` | `helmet` | 默认配置 | 生产环境启用默认 |
| `helmet({ contentSecurityPolicy: false })` | `helmet` | CSP 关闭 | 显式配置 CSP |
| `res.setHeader('X-Frame-Options', 'DENY')` | 原生 | 头值 | 默认 DENY/SAMEORIGIN |

### 调试/错误

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `app.use(errorhandler())` | `errorhandler` | 仅在 development | 生产环境禁用详细堆栈 |
| `res.status(500).send(err.stack)` | 业务代码 | 第 1 参数 | 生产环境仅返回错误码 |
| `NODE_ENV !== 'production'` 分支暴露调试接口 | 业务代码 | 环境变量 | 部署检查；CI 校验 |

### 依赖/环境

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `require(userControlledModule)` | 原生 | 第 1 参数 | 禁止用户控制模块路径 |
| `process.env[userInput]` | 原生 | 属性名 | 避免用户输入访问任意 env |
| `dotenv.config({ path: userPath })` | `dotenv` | `path` | 固定路径；禁止用户控制 |

---

## EXPORT

### 导出器

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `worksheet.addRow(userValues)` | `exceljs` | `userValues` 单元格值 | 公式前缀中和（前缀 `'`）；强制文本格式 |
| `stringify(records)` / `stringifier.write(row)` | `csv-stringify`、`fast-csv` | 记录字段值 | 写入前公式字符检测与中和 |
| `new Parser().parse(data)` | `json2csv` | 字段值 | 同上 |
| 手写 `` `${v1},${v2}` `` CSV 拼接 | 无 | 拼接字段 | 同上 |

### 公式注入模式

- 单元格值以 `=` `+` `-` `@` 开头被电子表格解释为公式
- DDE 载荷与 HYPERLINK 钓鱼链（同 dotnet 侧机制）

---

## PROMPT

### Prompt 组装与 RAG

| Sink API | 包名 | 可控参数位 | 参考 Barrier |
| --- | --- | --- | --- |
| `ChatPromptTemplate.fromMessages([...userContent])` | `langchain` | userContent 角色/内容 | 指令与数据分隔；输入消毒 |
| `openai.chat.completions.create({ messages })` | `openai` | messages 任意角色位 | system 角色不可被数据覆盖 |
| `streamText({ prompt, tools })` | `ai`（Vercel AI SDK） | prompt / tool 定义 | 工具权限最小化；输出人工确认门 |
| 向量检索结果直拼 prompt | `langchain` vectorstores | 检索文档内容 | 检索内容按数据处理；引用标注 |

### 工具/函数调用（含 MCP）

- 工具权限范围大于任务需要；MCP 工具无确认直接执行
- LLM 输出 JSON 被 `JSON.parse` 后直接驱动下游动作
