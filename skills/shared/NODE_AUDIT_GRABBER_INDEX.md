# Node.js 审计抓手索引

本文件用于统一 node-* Skill 的搜索关键字、优先枚举对象和常见落点，降低枚举阶段偏差。与 shared/DOTNET_AUDIT_GRABBER_INDEX.md 平级，方法论一致、生态关键字不同。

## 使用规则

- 先按 入口定义、绑定与参数、前置控制、敏感操作、安全配置 五层使用本索引检索
- 优先搜索 精确 API / 框架装饰器 / 中间件名，其次搜索 项目内封装命名、基础设施目录、工具函数、注册代码
- 每个 Skill 的 枚举规则（强制细化） 都应至少覆盖与本索引对应的关键词、对象类型和记录字段
- 如果项目存在二次封装，必须把封装名追加回本 Skill 输出，形成项目内私有抓手表
- 默认排除 node_modules/、dist/、build/、.next/、.nuxt/、coverage 目录，不纳入审计面；lockfile（package-lock.json / yarn.lock / pnpm-lock.yaml）例外必须纳入供应链审计

## 入口定义抓手

| 类型 | 优先关键字 | 重点记录 |
| ---- | ---- | ---- |
| 通用 Node | http.createServer, createServer, req.url, req.method | 原生路由分发、方法判断 |
| Express | express(), Router(), app.get, app.post, app.put, app.delete, app.patch, app.all, app.use, router.use | 路由模板、HTTP 方法、挂载前缀、中间件链 |
| NestJS | @Controller, @Get, @Post, @Put, @Delete, @Patch, @All, @UseGuards, @UseInterceptors | 装饰器路由、Guard/Interceptor 覆盖 |
| Next.js | app/api/**/route.{js,ts}, pages/api/**, export function GET, export function POST, NextRequest, middleware.ts | 文件约定路由、HTTP 方法导出、边缘中间件 |
| Koa | new Koa(), koa-router, router.get, router.post, app.use | 路由、ctx 传递 |
| Fastify | fastify.route, fastify.get, fastify.post, fastify.register, addHook | 路由注册、插件作用域、钩子 |
| Nuxt/Nitro | defineEventHandler, getQuery, readBody, server/api/** | 服务端入口、参数读取 |

## 绑定与参数抓手

| 类型 | 优先关键字 | 重点记录 |
| ---- | ---- | ---- |
| Express 系 | req.params, req.query, req.body, req.headers, req.cookies | 参数来源、名称映射 |
| Koa 系 | ctx.params, ctx.query, ctx.request.body, ctx.headers, ctx.cookies | 同上 |
| NestJS | @Body(), @Query(), @Param(), @Headers(), ValidationPipe | DTO 展开字段、校验管道白名单 |
| Next/Nuxt | await request.json(), request.nextUrl.searchParams, getQuery(), readBody(), getRouterParam() | 参数来源 |
| 文件输入 | multer, busboy, formidable, multipart | 文件名、dest、limits |

## 前置控制抓手

| 类型 | 优先关键字 | 重点记录 |
| ---- | ---- | ---- |
| 中间件链 | app.use, router.use, next(), Express 中间件顺序 | 挂载顺序、短路条件 |
| 鉴权中间件 | passport.authenticate, express-jwt, expressjwt, jwt.verify, express-session, cookie-session, next-auth, getServerSession | 鉴权覆盖范围、全局/路由级 |
| NestJS 控制面 | @UseGuards, AuthGuard, CanActivate, @Public | Guard 覆盖、匿名放行 |
| 安全头/CORS | helmet, cors(, Access-Control-Allow, CSP | 全局配置点 |

## 敏感操作抓手

| 类型 | 优先关键字 | 重点记录 |
| ---- | ---- | ---- |
| CMD | child_process, exec(, execSync(, spawn(, execFile(, shell: true | 命令构造、shell 参与度 |
| SQL | mysql, mysql2, pg, .query(, knex.raw, sequelize.query, typeorm | 查询来源、拼接片段 |
| NoSQL | mongoose, mongodb, .find(, $where, $regex, $gt | 查询对象来源、操作符注入字段 |
| SSRF | axios., fetch(, got(, request(, undici, http.get, https.get | URL 来源、重定向跟随 |
| 文件 | fs.readFile, fs.writeFile, fs.createReadStream, fs.createWriteStream, path.join, path.resolve, res.sendFile | 路径来源、规范化 |
| 模板 | ejs, pug, nunjucks, handlebars, mustache, res.render, .compile( | 模板源、拼接、模板名可控 |
| 表达式/反序列化 | eval(, new Function(, vm.runIn, node-serialize, unserialize, yaml.load | 执行上下文、输入来源 |
| 加密 | crypto.createHash, md5, sha1, createCipher(弃用), Math.random(用于 token) | 弱算法、随机源 |
| JWT/会话 | jsonwebtoken, jwt.sign, jwt.verify, jose | 算法钉死、密钥来源 |
| 归档解压 | adm-zip, extract-zip, tar, unzipper, yauzl | 解压落点、Zip Slip |

## 安全配置抓手

| 类型 | 优先关键字 | 重点记录 |
| ---- | ---- | ---- |
| 依赖清单 | package.json, package-lock.json, yarn.lock, pnpm-lock.yaml | 依赖版本、scripts 钩子、git/http 协议依赖 |
| 环境变量 | process.env, dotenv, .env | 密钥硬编码、env 文件入库 |
| 调试/错误 | NODE_ENV, app.get('env'), error.stack, console.log(敏感) | 错误外泄、调试开关 |
