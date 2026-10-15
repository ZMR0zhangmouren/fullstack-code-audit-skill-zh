# .NET Sink 参考（供 pipeline 与各子 Skill 统一对齐）

## SQL / ORM

### ADO.NET
- `System.Data.SqlClient.SqlCommand` — ExecuteReader / ExecuteScalar / ExecuteNonQuery / ExecuteXmlReader
- `System.Data.Common.DbCommand` — ExecuteReader / ExecuteScalar / ExecuteNonQuery
- `System.Data.SqlClient.SqlDataAdapter` — Fill / FillSchema / Update
- `Microsoft.Data.SqlClient.SqlCommand` — 同上（.NET Core 替代包）
- `System.Data.OleDb.OleDbCommand` — ExecuteReader / ExecuteNonQuery
- `System.Data.Odbc.OdbcCommand` — ExecuteReader / ExecuteNonQuery

### Entity Framework Core
- `RelationalDatabaseFacadeExtensions.ExecuteSqlRaw` / `ExecuteSqlRawAsync`
- `RelationalDatabaseFacadeExtensions.ExecuteSqlInterpolated` / `ExecuteSqlInterpolatedAsync`
- `RelationalQueryableExtensions.FromSqlRaw` / `FromSqlInterpolated`
- `Database.SqlQueryRaw<T>` / `SqlQuery<T>`（EF Core 7+）
- `DbContext.Database.GetDbConnection()` → 手动 CreateCommand
- `IQueryable.Where()` 接受字符串表达式（Dynamic LINQ）
- `IgnoreQueryFilters()` — 绕过全局过滤器（多租户/软删除）

### Dapper
- `SqlMapper.Query` / `Query<T>` / `QueryAsync<T>`
- `SqlMapper.Execute` / `ExecuteAsync`
- `SqlMapper.QueryMultiple` / `QueryMultipleAsync`
- `DynamicParameters` — 动态参数构造
- 字符串拼接 + `$"SELECT ... WHERE {userInput}"` 模式

### 其他 ORM / 数据访问
- `NHibernate.ISession.CreateSQLQuery` / `CreateQuery`（HQL 注入）
- `ServiceStack.OrmLite` — SqlExpression 字符串拼接
- `PetaPoco.Database.Query` / `Execute` / `Fetch`
- `RepoDB.DbConnection.ExecuteQuery` / `ExecuteNonQuery`

### 动态片段（无法参数化）
- 排序字段：`ORDER BY {column}`
- 表名/列名：`FROM {tableName}`
- IN 列表：`WHERE id IN ({ids})`
- 条件片段：`WHERE {dynamicCondition}`
- 分页：`OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY`

### 标识符注入（无法参数化，必须白名单）

- 排序字段：`ORDER BY {column}` — 外部可控列名/别名直接进入 ORDER BY 位
- 分组字段：`GROUP BY {column}` — 外部可控列名直接进入 GROUP BY 位
- 列名/表名动态替换：`SELECT {userColumn} FROM {userTable}` — 字段名或表名来自用户输入
- 嵌套过滤字段：`WHERE {dynamicColumn} = value` — 嵌套对象/字典的键名被用于 SQL 字段位，递归解析时子层独立校验
- 提示：参数化查询（`@param`）**不保护**标识符位，标识符位必须依赖白名单/枚举映射/严格校验器

## NoSQL

### MongoDB (.NET Driver)
- `IMongoCollection<T>.Find` / `FindAsync` — FilterDefinition 构造
- `Builders<T>.Filter` — Eq / Regex / Where（接受字符串表达式）
- `BsonDocument` 直接拼接查询条件
- `IMongoCollection<T>.Aggregate` — pipeline 构造
- `JsonFilterDefinition<T>` — 从 JSON 字符串构造 filter

### Azure Cosmos DB
- `Container.GetItemQueryIterator` — 自定义 SQL 查询字符串
- `QueryDefinition` — 字符串拼接构造
- `Container.ReadItemAsync` — partition key 注入

### Redis (StackExchange.Redis)
- `IDatabase.ScriptEvaluate` — Lua 脚本注入
- `IDatabase.Execute` — 原始命令拼接
- `ConnectionMultiplexer.GetServer().Keys()` — pattern 注入

### Elasticsearch (NEST / Elastic.Clients)
- `ElasticClient.Search<T>` — QueryRawJson
- `QueryContainer` 字符串拼接
- `LowLevelClient.Search<T>` — 原始 JSON body

## KQL / Kusto Query Language

### Azure Monitor Query SDK
- `LogsQueryClient.QueryWorkspaceAsync` — workspace + KQL 查询字符串
- `LogsQueryClient.QueryWorkspace` — 同步版本
- `LogsQueryClient.QueryResource` / `QueryResourceAsync` — 资源级查询
- `MetricsQueryClient.QueryResource` — Metrics 查询（KQL 变体）
- `Response<T>.Value` — 查询结果

### Application Insights SDK
- `TelemetryClient.Query` / `AnalyticsClient.Query` — 经典 AI 查询
- `ApplicationInsightsDataClient.QueryAsync` — 程序化查询接口

### 旧版 Log Analytics
- `Microsoft.Azure.OperationalInsights.OperationalInsightsDataClient.Query` — 旧版 SDK
- `Microsoft.Azure.OperationalInsights.OperationalInsightsDataClient.QueryAsync`

### KQL 注入模式
- KQL 字符串拼接：`$"traces | where message contains '{userInput}'"`
- 动态表名：`$"{userTable} | where ..."`
- 动态列名/字段名：`$"traces | project {userColumns}"`
- `extend` / `project` 动态字段：`$"traces | extend {userField} = ..."`
- `where` 条件片段拼接：`$"traces | where {userCondition}"`
- 管道注入：通过 `\n` 注入额外管道操作（`| take 10000\n| union (traces | take 10000)`）
- `contains` / `has` / `startswith` / `matches regex` 中混入未校验字符串

## CMD / 命令注入
- `ElasticClient.Search<T>` — QueryRawJson
- `QueryContainer` 字符串拼接
- `LowLevelClient.Search<T>` — 原始 JSON body

## CMD / 命令注入

### 进程启动
- `System.Diagnostics.Process.Start`
- `ProcessStartInfo` — FileName / Arguments / ArgumentList
- `ProcessStartInfo.UseShellExecute = true` — shell 解释风险

### Shell 调用模式
- `cmd.exe /c {command}` — Windows 命令拼接
- `powershell.exe -Command {script}` — PowerShell 注入
- `/bin/bash -c {command}` — Linux shell 拼接
- `RuntimeInformation.IsOSPlatform()` 条件分支下的 shell 调用

### 间接命令执行
- `Microsoft.Extensions.Hosting.IHostedService` — 后台任务中的命令执行
- `Hangfire.BackgroundJob.Enqueue` — 延迟执行中的参数传递
- `System.Management.ManagementObject.InvokeMethod` — WMI 命令
- `System.DirectoryServices.DirectoryEntry.Invoke` — ADSI 命令

## SSRF / 服务端请求伪造

### HttpClient 系列
- `HttpClient.SendAsync` / `GetAsync` / `PostAsync` / `PutAsync` / `DeleteAsync`
- `HttpClient.GetStringAsync` / `GetStreamAsync` / `GetByteArrayAsync`
- `IHttpClientFactory.CreateClient` — typed/named client
- `HttpMessageHandler` / `DelegatingHandler` — 请求拦截与修改

### 旧版 API
- `System.Net.WebRequest.Create` / `HttpWebRequest`
- `System.Net.WebClient.DownloadString` / `DownloadFile` / `UploadString`

### 第三方 HTTP 客户端
- `RestSharp.RestClient.Execute` / `ExecuteAsync`
- `Flurl.Http.FlurlClient` — GetAsync / PostAsync
- `Refit` — 动态 URL 构造

### 特殊场景
- Webhook 回调 URL — 用户提供的回调地址
- GraphQL 远程 schema stitching — 远程 URL 拉取
- PDF 生成器（wkhtmltopdf / Puppeteer）— URL 渲染
- 图片/头像下载 — 用户提供的图片 URL
- RSS/Atom feed 拉取 — 用户提供的 feed URL
- SOAP/WCF 客户端 — 动态 endpoint 地址
- `SmtpClient` — 用户控制的 SMTP 服务器地址
- `TcpClient` / `Socket` — 用户控制的 host:port

## XSS / 输出注入

### Razor 视图
- `Html.Raw()` — 禁用编码输出
- `IHtmlContent` / `HtmlString` — 标记为安全的 HTML
- `@:` 和 `<text>` 块中的未编码变量
- `TagHelper` 输出 — 自定义 TagHelper 的 output.Content
- `ViewComponent` / `Partial` / `DisplayTemplate` — 嵌套渲染

### Blazor
- `MarkupString` — 等价于 Html.Raw
- `RenderFragment` — 动态组件内容
- `IJSRuntime.InvokeAsync` — JS 互操作回填
- `NavigationManager.NavigateTo` — 客户端导航注入
- Prerender 混合渲染 — 服务端/客户端边界

### MVC / API 输出
- `Controller.Content()` — 自定义 Content-Type 输出
- `Controller.Json()` — JSON 序列化输出
- `FileContentResult` / `FileStreamResult` — 文件名注入
- `ContentResult` with `text/html` — 手工 HTML 拼接

### 编码器
- `HtmlEncoder` / `JavaScriptEncoder` / `UrlEncoder` — 自定义或禁用
- `JavaScriptEncoder.UnsafeRelaxedJsonEscaping` — 放松 JSON 编码
- `System.Text.Encodings.Web.TextEncoderSettings` — 自定义允许字符

### 前端交互
- `data-*` 属性注入 — 前端 JS 读取并执行
- `onclick` / `onload` 等事件属性拼接
- `<script>` 块中的服务端变量嵌入
- JSON 序列化后嵌入 `<script>` — XSS via JSON

## REDIR / 开放重定向

### ASP.NET Core
- `Controller.Redirect(url)` — 无验证重定向
- `Controller.LocalRedirect(url)` — 本地重定向（仍需验证）
- `Controller.RedirectToAction` / `RedirectToRoute` / `RedirectToPage`
- `Results.Redirect(url)` — Minimal API 重定向
- `HttpResponse.Redirect(url)`

### 认证流程
- `Challenge()` — 外部登录回跳 ReturnUrl
- `SignOut()` — 登出后跳转
- OAuth/OIDC `redirect_uri` / `post_logout_redirect_uri`
- SAML `RelayState` — 回跳地址

### 常见参数名
- `returnUrl` / `ReturnUrl` / `return_url`
- `redirect` / `redirectUrl` / `next` / `goto` / `continue`
- `callbackUrl` / `callback`

## CRLF / 响应头注入

### 响应头操作
- `HttpResponse.Headers.Append` / `Add`
- `HttpResponse.Headers["X-Custom"]` = userInput
- `Response.Cookies.Append` — Cookie 值注入

### 高风险头
- `Location` — 重定向头
- `Set-Cookie` — Cookie 注入
- `Content-Disposition` — 文件名注入
- `X-Forwarded-*` — 代理头透传
- 自定义安全头 — CSP / X-Frame-Options 覆盖

### 文件下载场景
- `Content-Disposition: attachment; filename="{userInput}"` — 文件名 CRLF
- 代理透传头 — 上游头未过滤直接写入响应

## FILE / 文件读取与路径穿越

### 文件读取 API
- `System.IO.File.ReadAllText` / `ReadAllBytes` / `ReadAllLines` / `ReadLines`
- `System.IO.File.OpenRead` / `Open` / `OpenText`
- `System.IO.FileStream` 构造函数
- `System.IO.StreamReader` 构造函数
- `System.IO.Path.Combine` — 路径拼接（不防穿越）
- `System.IO.Path.GetFullPath` — 规范化（可用于防御也可被绕过）

### ASP.NET 文件返回
- `PhysicalFile` / `PhysicalFileResult` — 物理路径文件返回
- `VirtualFileResult` — 虚拟路径文件返回
- `File(stream, contentType, fileName)` — 流式文件返回
- `IFileProvider.GetFileInfo` / `GetDirectoryContents`
- `StaticFileMiddleware` — 静态文件目录暴露

### 路径穿越模式
- `../` / `..\` — 目录遍历
- URL 编码：`%2e%2e%2f` / `%2e%2e%5c`
- 双重编码：`%252e%252e%252f`
- 空字节：`%00` 截断（旧版 .NET Framework）

## WRITE / 文件写入

### 写入 API
- `System.IO.File.WriteAllText` / `WriteAllBytes` / `WriteAllLines`
- `System.IO.File.AppendAllText` / `AppendAllLines`
- `System.IO.FileStream` — FileMode.Create / CreateNew / Append
- `System.IO.StreamWriter` — 构造函数与 Write/WriteLine
- `System.IO.BinaryWriter`

### 上传落盘
- `IFormFile.CopyTo` / `CopyToAsync` — 上传文件保存
- `IFormFile.OpenReadStream` → FileStream — 流式保存
- 临时文件 → 最终路径的移动/重命名

### 危险模式
- 用户控制文件名 + 写入 Web 可访问目录 → WebShell
- 用户控制路径 + 写入配置目录 → 配置覆盖
- 日志写入用户控制路径 → 日志注入 + 路径穿越

## UPLOAD / 文件上传

### 接收 API
- `IFormFile` / `IFormFileCollection` / `List<IFormFile>`
- `MultipartReader` — 手动解析 multipart
- `Request.Form.Files` — 直接访问文件集合
- `Request.Body` — 流式上传（无 multipart）

### 关键检查点
- 文件名：`IFormFile.FileName` — 客户端提供，可伪造
- 扩展名：白名单 vs 黑名单 vs 双扩展名绕过
- Content-Type：`IFormFile.ContentType` — 客户端提供，可伪造
- 文件大小：`IFormFile.Length` — 限制检查
- Magic bytes：文件头验证
- 落盘路径：是否在 Web 可访问目录
- 重命名策略：GUID vs 原始文件名

## ARCHIVE / 归档解压

### 解压 API
- `System.IO.Compression.ZipFile.ExtractToDirectory`
- `System.IO.Compression.ZipArchive` — 逐条目解压
- `ZipArchiveEntry.FullName` — 条目名（可含 `../`）
- `SharpZipLib` — ICSharpCode.SharpZipLib
- `SharpCompress` — 多格式归档库
- `System.Formats.Tar.TarFile.ExtractToDirectory`（.NET 7+）

### Zip Slip 模式
- `entry.FullName` 含 `../` → 写入目标目录外
- 符号链接条目 → 指向敏感文件
- 超长路径 → 路径截断

## XXE / XML 外部实体

### XML 解析器
- `System.Xml.XmlDocument.LoadXml` / `Load`
- `System.Xml.XPath.XPathDocument`
- `System.Xml.Linq.XDocument.Load` / `Parse`
- `System.Xml.XmlReader.Create` — 需检查 XmlReaderSettings
- `System.Xml.Xsl.XslCompiledTransform.Load` — XSLT 注入

### 关键配置
- `XmlReaderSettings.DtdProcessing` — Prohibit / Ignore / Parse
- `XmlReaderSettings.XmlResolver` — null 为安全
- `XmlDocument.XmlResolver` — 设为 null 禁用外部实体
- `XmlTextReader.DtdProcessing` — 旧版 API

### 危险默认值
- .NET Framework 4.5.1 以前：`XmlDocument` 默认允许 DTD
- .NET Framework 4.5.2+：默认禁用（但显式启用仍危险）
- .NET Core / .NET 5+：默认安全（DtdProcessing.Prohibit）

## DESER / 反序列化

### 高危序列化器（禁用类）
- `System.Runtime.Serialization.Formatters.Binary.BinaryFormatter`
- `System.Runtime.Serialization.NetDataContractSerializer`
- `System.Web.UI.LosFormatter` / `ObjectStateFormatter`（遗留 WebForms）
- `System.Runtime.Serialization.Formatters.Soap.SoapFormatter`

### 条件危险序列化器
- `Newtonsoft.Json` — `TypeNameHandling != None` 时危险
- `System.Text.Json` — 自定义 JsonConverter 可能引入类型混淆
- `System.Runtime.Serialization.DataContractSerializer` — 已知类型列表不当
- `System.Xml.Serialization.XmlSerializer` — 类型参数可控时危险
- `MessagePack` — 启用 typeless 模式时危险
- `protobuf-net` — 使用 `DynamicType` 时危险

### Gadget 链入口
- `ISerializable.GetObjectData` — 自定义序列化
- `IDeserializationCallback.OnDeserialization` — 反序列化回调
- `[OnDeserialized]` / `[OnDeserializing]` 属性标记的方法
- `TypeNameHandling.All` / `Auto` / `Objects` / `Arrays`

## TPL / 模板注入与表达式注入

### Razor 运行时编译
- `Microsoft.AspNetCore.Mvc.Razor.RuntimeCompilation` — 动态模板
- `RazorEngine` / `RazorLight` — 第三方 Razor 引擎
- 用户控制模板内容 → 服务端代码执行

### 表达式求值
- `Microsoft.CodeAnalysis.CSharp.Scripting.CSharpScript.EvaluateAsync`
- `System.Linq.Dynamic.Core` — Dynamic LINQ 表达式
- `System.Data.DataTable.Compute` — 表达式计算
- `System.Data.DataColumn.Expression` — 列表达式

### 其他模板引擎
- `Scriban` — 模板注入
- `Fluid` — Liquid 模板引擎
- `DotLiquid` — Liquid 模板引擎
- `Handlebars.NET` — Handlebars 模板
- 邮件模板引擎 — 用户控制模板变量或模板本身

## LDAP / 目录服务注入

### 查询 API
- `System.DirectoryServices.DirectorySearcher.Filter` — LDAP filter 拼接
- `System.DirectoryServices.DirectorySearcher.FindAll` / `FindOne`
- `System.DirectoryServices.AccountManagement.PrincipalContext`
- `System.DirectoryServices.Protocols.SearchRequest` — filter 参数

### 注入模式
- Filter 字符串拼接：`$"(uid={userInput})"` — 未转义特殊字符
- DN 拼接：`$"CN={userInput},DC=corp,DC=local"` — DN 注入
- 特殊字符：`*` / `(` / `)` / `\` / `NUL` — LDAP 元字符

## EXPR / 表达式注入（非模板）

### 求值入口
- `System.Linq.Dynamic.Core.DynamicQueryableExtensions` — Where / OrderBy / Select
- `Microsoft.CodeAnalysis.CSharp.Scripting.CSharpScript` — EvaluateAsync / RunAsync
- `System.Data.DataTable.Compute` — 表达式计算
- `System.Data.DataTable.Select` — filter 表达式
- `System.ComponentModel.DataAnnotations.RegularExpressionAttribute` — ReDoS

### 间接表达式
- `System.Reflection.Assembly.Load` / `LoadFrom` — 动态加载
- `Activator.CreateInstance` — 类型名可控
- `Type.GetType` — 类型字符串可控
- `MethodInfo.Invoke` — 反射调用

## AUTH / 认证与授权

### 认证机制
- `[Authorize]` / `[AllowAnonymous]` — 特性声明
- `AuthorizationPolicy` / `IAuthorizationRequirement` / `IAuthorizationHandler`
- `ClaimsPrincipal` / `ClaimsIdentity` — 身份信息
- JWT：`TokenValidationParameters` — 签名算法、issuer、audience 校验
- Cookie：`CookieAuthenticationOptions` — 过期、滑动窗口、加密

### 授权检查
- `IAuthorizationService.AuthorizeAsync` — 手动授权检查
- `HttpContext.User.IsInRole` / `HasClaim` — 角色/声明检查
- `[Authorize(Policy = "...")]` / `[Authorize(Roles = "...")]`
- 资源归属检查 — `userId == resource.OwnerId` 模式

### IDOR / 越权
- 路径参数 `{id}` 无归属校验
- 查询参数直接用于数据库查询无 owner 过滤
- 批量操作接口无逐条权限校验
- 管理接口仅前端隐藏无后端校验

## CSRF / 跨站请求伪造

### 防护机制
- `[ValidateAntiForgeryToken]` — MVC Action 级
- `[AutoValidateAntiforgeryToken]` — 全局自动
- `[IgnoreAntiforgeryToken]` — 豁免标记
- `IAntiforgery.ValidateRequestAsync` — 手动校验

### 绕过场景
- API Controller 默认不启用 Antiforgery
- `[HttpPost]` 无 `[ValidateAntiForgeryToken]`
- Content-Type 绕过：`text/plain` 不触发 CORS preflight
- 子域名 Cookie 注入 → token 覆盖

## SESS / 会话与 Cookie

### Cookie 配置
- `CookieOptions.HttpOnly` — 防 XSS 读取
- `CookieOptions.Secure` — 仅 HTTPS 传输
- `CookieOptions.SameSite` — 跨站限制
- `CookieOptions.Expires` / `MaxAge` — 过期策略
- `CookieOptions.Domain` / `Path` — 作用域

### JWT 配置
- `TokenValidationParameters.ValidateIssuerSigningKey` — 签名校验
- `TokenValidationParameters.ValidAlgorithms` — 算法白名单
- `TokenValidationParameters.ClockSkew` — 时间偏移
- `TokenValidationParameters.RequireExpirationTime` — 过期强制

### 会话管理
- `ISession` — 服务端会话
- 登录后 Session ID 轮换
- 登出时 Cookie / Token / Session 清理
- Refresh Token 轮换与撤销

## CFG / 安全配置

### CORS
- `AddCors` / `UseCors` — CORS 策略
- `AllowAnyOrigin` + `AllowCredentials` — 危险组合
- `WithOrigins("*")` — 通配符
- `SetIsOriginAllowed(_ => true)` — 全部允许

### 错误处理
- `UseDeveloperExceptionPage` — 开发异常页（生产泄露）
- `UseExceptionHandler` — 自定义异常处理
- `app.Environment.IsDevelopment()` — 环境判断
- 详细错误信息返回给客户端

### 安全头
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY` / `SAMEORIGIN`
- `Content-Security-Policy`
- `Strict-Transport-Security`（HSTS）
- `X-XSS-Protection`（已废弃但仍需检查）
- `Referrer-Policy`
- `Permissions-Policy`

### 危险开关
- `Kestrel.Limits` — 请求大小、超时
- `ForwardedHeadersOptions.ForwardLimit` — 代理信任
- `HostFilteringOptions` — 主机头过滤
- `JsonSerializerOptions.PropertyNameCaseInsensitive` — 大小写混淆
- `appsettings.Development.json` 覆盖生产配置

## CRYPTO / 加密与密钥

### 弱算法
- `MD5` / `SHA1` — 哈希碰撞
- `DES` / `3DES` / `RC2` / `RC4` — 弱加密
- `RNGCryptoServiceProvider` vs `RandomNumberGenerator.Create` — 随机数

### 密钥管理
- 硬编码密钥 / 连接字符串
- `appsettings.json` 中的明文密钥
- `IDataProtectionProvider` — 数据保护 API
- `X509Certificate2` — 证书加载与私钥保护
- Azure Key Vault / AWS Secrets Manager 集成

### 加密模式
- `CipherMode.ECB` — 不安全模式
- `PaddingMode.PKCS7` — padding oracle
- IV 重用 / 固定 IV
- `Aes.Create()` — 默认参数是否安全

## LOGIC / 业务逻辑

### Mass Assignment
- `[Bind]` / `[BindNever]` — 绑定控制
- `TryUpdateModel` / `TryUpdateModelAsync` — 模型更新
- DTO 缺少 `[JsonIgnore]` / `[BindNever]` 的敏感字段
- `JsonPatchDocument.ApplyTo` — JSON Patch 覆盖

### 竞态条件
- `lock` / `Monitor` / `Semaphore` — 并发控制
- 数据库乐观锁 / 悲观锁
- 余额/库存/计数器的 check-then-act 模式
- 文件操作 TOCTOU（Time-of-check to time-of-use）

### 状态机缺陷
- 订单/支付/审批流程的状态跳转
- 枚举值直接从请求绑定 → 非法状态转换
- 缺少前置状态校验的操作接口

## LOG / 安全日志

### 日志注入
- `ILogger.LogInformation($"{userInput}")` — 日志伪造
- 换行符注入 → 伪造日志条目
- 格式化字符串注入

### 敏感信息泄露
- 密码、Token、密钥写入日志
- 完整请求体/响应体记录
- 异常堆栈中的连接字符串
- PII 数据未脱敏

### 审计覆盖
- 认证成功/失败事件
- 授权拒绝事件
- 敏感操作（删除、修改权限、导出）事件
- 管理员操作事件

## QUERY / 非 SQL 查询语言

### SOQL（Salesforce 生态）
- `ForceClient.QueryAsync<T>(soql)` — SOQL 查询字符串
- `SforceService.query(soql)` / REST `/query?q=` — 查询参数直拼
- SOQL 字符串拼接：`$"SELECT Id FROM Account WHERE Name = '{userInput}'"`

### OData
- OData URL 拼接：`$filter=` / `$orderby=` / `$select=` / `$expand=` 参数含用户输入
- `ODataClient` / `Container` LINQ 提供者逃逸为原始查询字符串
- Web API OData：`[EnableQuery]` + 原始查询选项直通

### FetchXML（Dynamics 365 生态）
- `QueryExpression` 条件值来自用户输入（`new ConditionExpression(attr, op, userInput)`）
- FetchXML 字符串拼接：`<filter><condition value='{userInput}'>` 直拼
- `RetrieveMultiple(QueryBase)` / FetchXML 执行入口

### 注入模式
- 查询片段拼接进入可执行结构（条件值、过滤表达式、查询体）
- 结构化 API 误用：强类型查询对象的条件值未做类型/范围校验

## EXPORT / 电子表格导出

### CSV/Excel 生成器
- `CsvWriter`（CsvHelper）写入字段值未做公式中和
- `ExcelPackage` / `EPPlus`、`ClosedXML`、`NPOI` 单元格直写用户数据且未设文本格式
- `StringWriter` / 手写 CSV 拼接：`string.Join(",", values)` 直出

### 公式注入模式
- 单元格值以 `=` `+` `-` `@` 开头被电子表格解释为公式
- DDE 载荷：`=cmd|' /C calc'!A1` 类命令执行链
- 超链接注入：`HYPERLINK("https://evil", "点击")` 钓鱼链

## PROMPT / AI 提示组装与工具调用

### Prompt 组装
- PromptTemplate / 模板字符串插值含用户输入（Semantic Kernel `KernelFunction`、Azure.AI.OpenAI `ChatCompletion`）
- RAG 管道：向量检索结果（不可信文档内容）直拼入 prompt 上下文
- System prompt 与数据边界缺失：检索/工具返回内容置于系统指令角色位

### 工具/函数调用
- Function calling 定义：工具权限范围大于任务需要
- LLM 输出 JSON 被解析并直接驱动下游动作（查询、发送、执行）
- 输出未做校验/人工确认门即进入敏感操作
