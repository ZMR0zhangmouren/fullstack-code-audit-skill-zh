# 证据点 ID 统一字典（.NET）

说明：

- 本文件用于让 dotnet-route-tracer 的 Sink Evidence Checklist 与各子 Skill 的证据引用实现字段级同名对齐。
- 没有 trace 时，允许用静态源码证据对齐相同 EVID_* 键名，但结论只能是 ⚠️待验证 或 🔍环境依赖。

## SQL

- EVID_SQL_EXEC_POINT：SQL 执行点证据
- EVID_SQL_STRING_CONSTRUCTION：SQL 字符串构造或 RawSQL 证据
- EVID_SQL_USER_PARAM_TO_SQL_FRAGMENT：用户参数到 SQL 片段映射证据

## NOSQL

- EVID_NOSQL_QUERY_CONSTRUCTION：NoSQL 查询构造点证据
- EVID_NOSQL_USER_INPUT_INTO_QUERY_STRUCTURE：用户输入进入查询结构证据
- EVID_NOSQL_OPERATOR_INJECTION_FIELDS：操作符注入字段证据

## KQL

- EVID_KQL_EXEC_POINT：KQL 执行点证据（如 `LogsQueryClient.QueryWorkspaceAsync`、`QueryResource`、`OperationalInsightsDataClient.Query`）
- EVID_KQL_STRING_CONSTRUCTION：KQL 查询字符串构造或拼接证据
- EVID_KQL_USER_PARAM_TO_KQL_FRAGMENT：用户输入到 KQL 片段或管道操作映射证据

## CMD

- EVID_CMD_EXEC_POINT：Process.Start 或 shell 执行点证据
- EVID_CMD_COMMAND_STRING_CONSTRUCTION：命令参数构造证据
- EVID_CMD_USER_PARAM_TO_CMD_FRAGMENT：用户输入到命令片段映射证据

## SSRF

- EVID_SSRF_URL_NORMALIZATION：URL 归一化与拼接证据
- EVID_SSRF_FINAL_URL_HOST_PORT：最终请求 URL / Host / Port 证据
- EVID_SSRF_DNSIP_AND_INNER_BLOCK：DNS / IP 解析与内网拦截证据

## XSS

- EVID_XSS_OUTPUT_POINT：输出点证据
- EVID_XSS_USER_INPUT_INTO_OUTPUT：用户输入进入输出上下文证据
- EVID_XSS_ESCAPE_OR_RAW_CONTROL：编码、Raw 输出或安全模板控制证据

## DOM-XSS

- EVID_DOMXSS_SINK_OUTPUT_POINT：客户端输出 sink 点证据（如 `innerHTML`、`document.write`、`location`、`eval` 或 JS 插值输出）
- EVID_DOMXSS_USER_INPUT_SOURCE：用户输入来源证据（如 URL 参数、fragment、postMessage、服务端注入 JS 上下文的数据）
- EVID_DOMXSS_ENCODING_SANITIZE_PROOF：输出前编码 / 净化 / 安全 API 使用证据（如 `textContent`、DOMPurify、编码函数）

## REDIR

- EVID_REDIR_OUTPUT_POINT：重定向输出点证据
- EVID_REDIR_DEST_SOURCE_MAPPING：目标地址来源映射证据
- EVID_REDIR_DEST_VALIDATION_NORMALIZATION：目标校验与归一化证据

## CRLF

- EVID_CRLF_OUTPUT_POINT：响应头或 Cookie 输出点证据
- EVID_CRLF_USER_INPUT_INTO_HEADER_COOKIE：用户输入进入 header / cookie 值证据
- EVID_CRLF_CONTROL_CHAR_FILTERING_ENCODING：控制字符过滤、编码与宿主拦截证据

## FILE

- EVID_FILE_RESOLVED_TARGET：最终读取目标路径证据
- EVID_FILE_PATH_NORMALIZATION：路径拼接与规范化证据
- EVID_FILE_EXECUTION_BOUNDARY：读取与执行边界证据

## WRITE

- EVID_WRITE_CALLSITE：写入调用点证据
- EVID_WRITE_DESTPATH_JOIN_AND_NORMALIZATION：目的路径规范化证据
- EVID_WRITE_CONTENT_SOURCE_INTO_WRITE：写入内容来源映射证据
- EVID_WRITE_EXECUTION_ACCESSIBILITY_PROOF：写后可访问性 / 可执行性证据

## UPLOAD

- EVID_UPLOAD_DESTPATH：保存路径证据
- EVID_UPLOAD_FILENAME_EXTENSION_PARSING_SANITIZE：文件名与扩展名处理证据
- EVID_UPLOAD_ACCESSIBILITY_PROOF：落盘后可访问面证据

## ARCHIVE

- EVID_ARCHIVE_EXTRACT_CALLSITE：解压调用点证据
- EVID_ARCHIVE_ENTRY_NAME_SOURCE：归档条目名来源证据
- EVID_ARCHIVE_FINAL_TARGET：最终解析目标路径证据

## XXE

- EVID_XXE_PARSER_CALL：XML 解析器调用点证据
- EVID_XXE_INPUT_SOURCE：输入来源证据
- EVID_XXE_ENTITY_DOCTYPE_SAFETY_AND_ECHO：DOCTYPE / Entity 安全选项与回显证据

## DESER

- EVID_DESER_CALLSITE：反序列化调用点证据
- EVID_DESER_INPUT_SOURCE：输入来源证据
- EVID_DESER_OBJECT_TYPE_MAGIC_TRIGGER_CHAIN：类型信息与后续敏感链路证据

## TPL

- EVID_TPL_ENGINE_RENDER_OR_PARSE_ENTRY：模板引擎入口证据
- EVID_TPL_TEMPLATE_OR_EXPR_CONTROL：模板名或表达式可控性证据
- EVID_TPL_EXEC_CHAIN_ENTRY：模板编译、求值或执行链入口证据

## SSTI

- EVID_SSTI_TEMPLATE_SOURCE：模板来源可控性证据
- EVID_SSTI_SANDBOX_ESCAPE：沙箱逃逸证据
- EVID_SSTI_USER_INPUT_TO_TEMPLATE：用户输入到模板注入点证据
- EVID_SSTI_RENDER_EXEC_CHAIN：模板渲染执行链证据

## LDAP

- EVID_LDAP_EXEC_POINT：LDAP 查询执行点证据
- EVID_LDAP_FILTER_STRING_CONSTRUCTION：Filter / DN 构造证据
- EVID_LDAP_USER_PARAM_TO_FILTER_FRAGMENT：用户输入到 Filter 片段映射证据

## XPATH

- EVID_XPATH_EXEC_POINT：XPath 查询执行点证据（如 `XPathNavigator.Select`、`XmlNode.SelectNodes`）
- EVID_XPATH_EXPR_CONSTRUCTION：XPath 表达式构造、拼接或插值证据
- EVID_XPATH_USER_PARAM_TO_XPATH_FRAGMENT：用户输入到 XPath 片段或谓词映射证据

## EXPR

- EVID_EXPR_EVAL_ENTRY：表达式求值入口证据
- EVID_EXPR_EXPR_CONTROL：表达式字符串可控性证据
- EVID_EXPR_EXEC_CHAIN_ENTRY：求值结果进入敏感语义证据

## AUTH

- EVID_AUTH_PATH_PROTECTED_MATCH：受保护入口匹配证据
- EVID_AUTH_TOKEN_DECODE_JUDGMENT：认证票据解析与判断证据
- EVID_AUTH_PERMISSION_CHECK_EXEC：Policy / Role / Claim 检查证据
- EVID_AUTH_IDOR_OWNERSHIP_CONDITION：资源归属校验证据
- EVID_AUTH_ENUM_ENDPOINT_SURFACE：登录/找回/注册端点枚举面证据
- EVID_AUTH_ENUM_OBSERVABLE_DIFF：成功/失败/不存在账号间可观察差异（状态码/响应体/时序至少一项）证据
- EVID_AUTH_ENUM_IMPACT_CONFIRM：账号存在性或认证状态可被推断的影响闭合证据

## CSRF

- EVID_CSRF_STATE_CHANGE_HANDLER_EXEC：状态变更入口执行证据
- EVID_CSRF_TOKEN_SOURCE：CSRF token 生成来源证据
- EVID_CSRF_TOKEN_VERIFY：服务端校验证据
- EVID_CSRF_BYPASS_BRANCH：绕过分支证据

## SESS

- EVID_SESS_COOKIE_FLAGS：Cookie flags 证据
- EVID_SESS_TICKET_REGEN_ROTATION：登录后票据轮换证据
- EVID_SESS_JWT_VERIFY_CLAIMS：JWT claims 与签名校验证据
- EVID_SESS_LOGOUT_CLEAR：退出清理证据

## CFG

- EVID_CFG_CONFIG_LOCATION：配置位置证据
- EVID_CFG_RUNTIME_SETTING_CODE：运行时设置代码证据
- EVID_CFG_IMPACT_ASSOCIATION：配置影响点关联证据
- EVID_CFG_SECURITY_SWITCH_EVIDENCE：关键安全开关证据
- EVID_CFG_SENSITIVE_ENDPOINT_EXPOSURE：路由/配置/元数据端点未授权可访问面证据
- EVID_CFG_INTERNAL_INFO_DISCLOSURE：响应实际暴露内部实现/部署配置证据（非仅端点存在）
- EVID_CFG_SECRET_MATERIAL_IN_RESPONSE：响应中检出 secret material 的凭据泄露证据

## CRYPTO

- EVID_CRYPTO_ALGO_SELECTION：算法选择证据
- EVID_CRYPTO_KEY_SOURCE：密钥来源证据
- EVID_CRYPTO_MODE_PADDING_RANDOMNESS：模式、填充、随机性证据
- EVID_CRYPTO_REPLAY_FRESHNESS_ABSENT：签名验证入口缺少 nonce/timestamp/replay cache freshness 校验证据
- EVID_CRYPTO_REPLAY_ACCEPTANCE：同一签名请求二次提交被接受的重放实证
- EVID_CRYPTO_REPLAY_IMPACT_CONFIRM：重放导致越权操作/状态变更的影响闭合证据

## SUPPLY（供应链）

- EVID_SUPPLY_CVE_MATCH：依赖版本与已知 CVE/GHSA 数据库命中记录证据（CVE ID、影响版本区间、当前/locked 版本、修复版本）
- EVID_SUPPLY_UNSAFE_SOURCE：包源协议或来源风险证据（源 URL、协议类型、认证方式）
- EVID_SUPPLY_SIGNATURE_GAP：签名验证缺失或配置缺陷证据（allowUntrustedRoot、trustedSigners 未配置）
- EVID_SUPPLY_TRANSITIVE_PATH：传递依赖可利用路径证据（直接依赖 → 传递依赖 → 可利用接口）
- EVID_SUPPLY_SPOOF_DEP：依赖混淆/typosquatting/幽灵依赖嫌疑证据（包名相似度、来源声明位置）
- EVID_SUPPLY_TOOL_OUTPUT：工具扫描原始输出证据（dotnet list package --vulnerable / osv-scanner / npm audit）
- EVID_SUPPLY_LOCK_GAP：lockfile 缺失或版本漂移证据（声明位置、range、locked 版本）

## LOGIC / FS / LOG

- EVID_LOGIC_STATE_TRANSITION：状态流转与业务条件证据
- EVID_LOGIC_NUMERIC_USER_SOURCE：用户可控数值进入算术运算的源定位证据
- EVID_LOGIC_ARITHMETIC_POINT：加减乘/长度偏移/货币积分换算等算术运算点证据
- EVID_LOGIC_OVERFLOW_IMPACT：溢出或边界绕过导致逻辑失败/可用性损失的影响证据
- EVID_FS_TOCTOU_OR_LINK_BEHAVIOR：文件系统竞态或链接行为证据
- EVID_LOG_EVENT_COVERAGE_AND_SENSITIVE_DATA：日志覆盖与敏感信息证据
- EVID_LOG_TAMPERABLE_FIELD_SOURCE：可控 header/cookie/审计字段实际写入审计记录的写入路径证据
- EVID_LOG_IDENTITY_MISATTRIBUTION_IMPACT：身份冒用/错误归因影响闭合证据
- EVID_LOG_FLOODING_EXHAUSTION_PATH：高频/大体量写入与审计存储耗尽因果链证据

## HTTP DESYNC

- EVID_DESYNC_CL_T_CONFLICT：Content-Length 与 Transfer-Encoding 冲突证据
- EVID_DESYNC_PROXY_INCONSISTENCY：代理层不一致性证据
- EVID_DESYNC_REQUEST_PREFIX_TRUNCATION：请求前缀截断证据
- EVID_DESYNC_HTTP2_SMUGGLING：HTTP/2 请求走私证据
- EVID_DESYNC_RESPONSE_TAIL_INJECTION：响应尾部注入证据

## SECOND-ORDER

- EVID_SECOND_ORDER_STORAGE：数据二次存储证据
- EVID_SECOND_ORDER_TRIGGER：二次触发执行证据
- EVID_SECOND_ORDER_STORE_ENTRANCE：存储入口点证据
- EVID_SECOND_ORDER_TRIGGER_ENTRANCE：触发入口点证据
- EVID_SECOND_ORDER_DATA_FLOW_MAPPING：存储到触发的数据流映射证据

## QUERY（非 SQL 查询语言注入）

- EVID_QUERY_EXEC_POINT：非 SQL 查询执行点证据（如 SOQL 查询提交、OData 请求执行、FetchXML 执行）
- EVID_QUERY_STRING_CONSTRUCTION：非 SQL 查询字符串/结构构造或拼接证据
- EVID_QUERY_USER_PARAM_TO_FRAGMENT：用户输入到查询片段、条件或结构映射证据

## EXPORT（电子表格公式注入）

- EVID_EXPORT_FIELD_USER_CONTROLLED：导出字段来自用户控制数据的证据
- EVID_EXPORT_FORMULA_SINK：导出生成/单元格写入点证据（CSV/Excel 生成器、拼接写入）
- EVID_EXPORT_INTERPRETATION_PATH：导出内容会被电子表格解释为公式/命令/链接的路径证据

## PROMPT（AI 提示注入）

- EVID_PROMPT_UNTRUSTED_CONTENT：不可信内容（用户输入/RAG 检索/工具返回）进入 prompt 上下文的证据
- EVID_PROMPT_BOUNDARY_CROSSING：不可信内容跨越指令/数据边界（system/developer/user/data 角色混淆）的证据
- EVID_PROMPT_TOOL_PERMISSION_SCOPE：工具/函数调用权限范围与越权可行性的证据
- EVID_PROMPT_OUTPUT_HANDLING：LLM 输出被解析、执行或驱动下游动作的处理证据

## NODE 命名空间（EVID_NODE_*）

### PROTO（原型链污染）
- EVID_NODE_PROTO_MERGE_SINK：递归合并/深拷贝汇聚点证据（merge/assign/clone/extend 等）
- EVID_NODE_PROTO_MAGIC_KEY_CONTROL：`__proto__`/`constructor`/`prototype` 键名可控证据
- EVID_NODE_PROTO_KEY_FILTER_ABSENT_OR_BYPASS：键名过滤缺失或可绕过证据
- EVID_NODE_PROTO_GADGET_TRIGGER：污染后链接触发面证据（选项对象/模板引擎/child_process 选项等）

### CMD
- EVID_NODE_CMD_EXEC_POINT：child_process.exec/execSync/spawn(shell:true)/execFile 调用点证据
- EVID_NODE_CMD_STRING_CONSTRUCTION：命令字符串拼接证据
- EVID_NODE_CMD_USER_PARAM_TO_CMD：用户输入到命令片段映射证据
- EVID_NODE_CMD_ARG_ARRAY_OR_ALLOWLIST：参数数组化/白名单防护证据

### SSRF
- EVID_NODE_SSRF_HTTP_CALL_POINT：服务端 HTTP 客户端调用点证据（axios/fetch/got/request/undici/http.get）
- EVID_NODE_SSRF_URL_CONSTRUCTION：URL 拼接与归一化证据
- EVID_NODE_SSRF_ALLOWLIST：协议/主机/IP allowlist 与 DNS 解析后校验证据
- EVID_NODE_SSRF_REDIRECT_FOLLOW：重定向跟随配置证据（followRedirects/maxRedirects）

### NOSQL
- EVID_NODE_NOSQL_QUERY_POINT：驱动/ODM 查询调用点证据
- EVID_NODE_NOSQL_RAW_OBJECT_PASS：req.body/req.query 原样对象直通查询证据
- EVID_NODE_NOSQL_OPERATOR_INJECTION：$where/$regex/$gt 等操作符进入查询结构证据
- EVID_NODE_NOSQL_TYPE_COERCE_GUARD：类型强制/Schema 校验防护证据

### UPLOAD
- EVID_NODE_UPLOAD_MIDDLEWARE_CONFIG：multer/busboy/formidable 配置点证据
- EVID_NODE_UPLOAD_FILENAME_SANITIZE：文件名净化/路径穿越防护证据
- EVID_NODE_UPLOAD_FILTER_LIMITS：fileFilter/limits/后缀白名单证据
- EVID_NODE_UPLOAD_ACCESSIBILITY：落盘后可访问/可执行面证据

### XSS
- EVID_NODE_XSS_OUTPUT_POINT：HTML 输出点证据（res.send 拼接/res.render/dangerouslySetInnerHTML/v-html）
- EVID_NODE_XSS_USER_INPUT_INTO_OUTPUT：用户输入进入输出上下文证据
- EVID_NODE_XSS_ENCODE_OR_SANITIZE：输出编码/净化（escape-html/DOMPurify/模板自动转义）证据
- EVID_NODE_XSS_SSR_HYDRATION：SSR 注水注入面证据（__NEXT_DATA__/__NUXT__）

### SSTI
- EVID_NODE_SSTI_RENDER_POINT：模板引擎 render/compile 调用点证据（ejs/pug/nunjucks/handlebars）
- EVID_NODE_SSTI_TEMPLATE_CONCAT：模板串拼接用户输入证据（非表达式参数化）
- EVID_NODE_SSTI_TEMPLATE_NAME_CONTROL：模板名/引擎选项可控证据

### SESS（会话与 JWT）
- EVID_NODE_SESS_JWT_SIGN_VERIFY_CONFIG：jwt.sign/jwt.verify 配置证据
- EVID_NODE_SESS_JWT_ALG_PINNED：算法钉死/拒绝 alg:none 证据
- EVID_NODE_SESS_SECRET_SOURCE：密钥来源与强度证据
- EVID_NODE_SESS_COOKIE_FLAGS：Cookie HttpOnly/Secure/SameSite/Domain/Path 证据
- EVID_NODE_SESS_LIFECYCLE：过期/注销/会话固定处理证据

### NODE-AUTH（认证与枚举）
- EVID_NODE_AUTH_ENUM_ENDPOINT_SURFACE：登录/找回/注册端点枚举面证据
- EVID_NODE_AUTH_ENUM_OBSERVABLE_DIFF：成功/失败/不存在账号间可观察差异（状态码/响应体/时序至少一项）证据
- EVID_NODE_AUTH_ENUM_IMPACT_CONFIRM：账号存在性或认证状态可被推断的影响闭合证据

### CFG（框架配置与控制面）
- EVID_NODE_CFG_SECURITY_SWITCH：安全开关/默认配置证据（helmet、secure 默认值、fail-open 开关、CORS 通配+credentials）
- EVID_NODE_CFG_RUNTIME_SETTING：运行时配置证据（process.env、dotenv、.env 泄露、debug 开关）
- EVID_NODE_CFG_MIDDLEWARE_ORDER：中间件/Guard/Interceptor 顺序与短路条件证据
- EVID_NODE_CFG_SSR_MODE：SSR/同构渲染模式配置证据（渲染模式、注水数据、边缘运行时）
- EVID_NODE_CFG_ERR_HANDLER：错误处理与堆栈泄露证据（全局异常捕获、错误响应含内部路径/版本指纹）
- EVID_NODE_CFG_SENSITIVE_ENDPOINT_EXPOSURE：路由/配置/元数据端点未授权可访问面证据
- EVID_NODE_CFG_INTERNAL_INFO_DISCLOSURE：响应实际暴露内部实现/部署配置证据（非仅端点存在）
- EVID_NODE_CFG_SECRET_MATERIAL_IN_RESPONSE：响应中检出 secret material 的凭据泄露证据

### SQL
- EVID_NODE_SQL_QUERY_POINT：驱动/ORM 查询调用点证据（mysql/mysql2/knex/sequelize/pg/prisma）
- EVID_NODE_SQL_STRING_CONCAT：SQL 文本拼接证据（+ 拼接/模板字符串插值/knex.raw/sequelize.literal/prisma.$queryRawUnsafe）
- EVID_NODE_SQL_PARAM_BINDING_GUARD：占位符/参数绑定防护证据（execute(?)、prepared statement）
- EVID_NODE_SQL_STRUCTURE_POSITION：标识符/排序键等结构位置进入 SQL 证据

### XXE
- EVID_NODE_XXE_PARSE_POINT：XML 解析调用点证据（xml2js/sax/fast-xml-parser/libxmljs）
- EVID_NODE_XXE_EXTERNAL_ENTITY_FLAG：外部实体/DOCTYPE 处理配置证据（resolveEntities/noent/DTD 开关）
- EVID_NODE_XXE_SAFE_PARSER_ALTERNATIVE：安全解析配置证据（禁 DTD/禁外部实体/strict 模式）

### DESER
- EVID_NODE_DESER_UNSAFE_CALL：不安全反序列化调用点证据（node-serialize.unserialize/yaml.load unsafe/serialize-javascript 反序列化/funcster）
- EVID_NODE_DESER_INPUT_CONTROL：反序列化数据来源可控性证据
- EVID_NODE_DESER_GADGET_REACH：反序列化后函数/构造触发可达性证据
- EVID_NODE_DESER_SAFE_ALTERNATIVE：安全替代/Schema 校验防护证据（JSON.parse + 固定 schema 等）

### CSRF
- EVID_NODE_CSRF_STATE_CHANGE_ENDPOINT：状态变更端点证据（POST/PUT/DELETE 且产生副作用）
- EVID_NODE_CSRF_TOKEN_CHECK：CSRF token/origin/referer 校验存在性与实现证据（csurf 移除后自建防护）
- EVID_NODE_CSRF_COOKIE_SAMESITE：Cookie SameSite/签名配置证据（与 SESS 组联动）
- EVID_NODE_CSRF_SECOND_CONFIRM：敏感操作二次确认证据

### CRYPTO
- EVID_NODE_CRYPTO_WEAK_ALGO：弱算法/弱模式调用点证据（md5/sha1/des/ecb/createCipheriv 弱参数）
- EVID_NODE_CRYPTO_KEY_SOURCE：密钥来源与硬编码证据（.env/源码字面量/密钥管理服务）
- EVID_NODE_CRYPTO_RANDOM_SOURCE：随机数来源证据（Math.random 用于安全场景 vs crypto.randomBytes）
- EVID_NODE_CRYPTO_HASH_MODE：口令哈希方案证据（pbkdf2/scrypt/bcrypt/argon2 vs 单次 sha256）
- EVID_NODE_CRYPTO_REPLAY_FRESHNESS_ABSENT：签名验证入口缺少 nonce/timestamp/replay cache freshness 校验证据
- EVID_NODE_CRYPTO_REPLAY_ACCEPTANCE：同一签名请求二次提交被接受的重放实证
- EVID_NODE_CRYPTO_REPLAY_IMPACT_CONFIRM：重放导致越权操作/状态变更的影响闭合证据

### LOGIC
- EVID_NODE_LOGIC_RACE_WINDOW：竞态窗口证据（检查与使用非原子、check-then-act）
- EVID_NODE_LOGIC_TOCTOU_PAIR：TOCTOU 对象证据（校验点与使用点分离）
- EVID_NODE_LOGIC_WORKFLOW_BYPASS：流程跳步/绕过证据（客户端可控状态机、步骤参数直通）
- EVID_NODE_LOGIC_LIMIT_CONTROL：金额/数量/次数限制服务端复核证据
- EVID_NODE_LOGIC_NUMERIC_USER_SOURCE：用户可控数值进入算术运算的源定位证据
- EVID_NODE_LOGIC_ARITHMETIC_POINT：加减乘/长度偏移/货币积分换算等算术运算点证据
- EVID_NODE_LOGIC_OVERFLOW_IMPACT：溢出或边界绕过导致逻辑失败/可用性损失的影响证据

### LOG
- EVID_NODE_LOG_INJECTION_POINT：日志写入点含用户输入证据（winston/pino/console 模板串）
- EVID_NODE_LOG_SENSITIVE_DATA：敏感数据入日志证据（密码/token/PII 明文）
- EVID_NODE_LOG_TAMPER_SURFACE：日志伪造/注入面证据（换行/结构化字段污染）
- EVID_NODE_LOG_AUDIT_TRAIL：关键操作审计留存证据
- EVID_NODE_LOG_TAMPERABLE_FIELD_SOURCE：可控 header/cookie/审计字段实际写入审计记录的写入路径证据
- EVID_NODE_LOG_IDENTITY_MISATTRIBUTION_IMPACT：身份冒用/错误归因影响闭合证据
- EVID_NODE_LOG_FLOODING_EXHAUSTION_PATH：高频/大体量写入与审计存储耗尽因果链证据

### FILE_READ
- EVID_NODE_FILE_READ_POINT：文件读取调用点证据（fs.readFile/readFileSync/createReadStream/sendFile）
- EVID_NODE_FILE_READ_PATH_CONSTRUCTION：读取路径构造证据（path.join/拼接用户输入）
- EVID_NODE_FILE_READ_TRAVERSAL_GUARD：穿越防护证据（resolve 后前缀校验/allowlist）
- EVID_NODE_FILE_READ_STATIC_ROOT：静态目录边界证据（express.static/serve-static 挂载范围）

### FILE_WRITE
- EVID_NODE_FILE_WRITE_POINT：文件写入调用点证据（fs.writeFile/writeFileSync/appendFile/createWriteStream）
- EVID_NODE_FILE_WRITE_PATH_CONSTRUCTION：写入路径构造证据（上传文件名/参数进路径）
- EVID_NODE_FILE_WRITE_OVERWRITE_PROTECTION：覆盖/追加防护证据（已有文件冲突策略、flag 配置）
- EVID_NODE_FILE_WRITE_CONTENT_CONTROL：写入内容可控性证据（内容/扩展名/落盘目录）

### ARCHIVE（归档解压）
- EVID_NODE_ARCHIVE_EXTRACT_POINT：解压调用点证据（unzipper/adm-zip/yauzl/tar-stream/extract-zip）
- EVID_NODE_ARCHIVE_ENTRY_PATH_SANITIZE：条目路径净化证据（entryName `../`、绝对路径、盘符）
- EVID_NODE_ARCHIVE_ZIP_SLIP_GUARD：Zip Slip 防护证据（目标根前缀校验/符号链接策略）

### OPEN_REDIRECT
- EVID_NODE_REDIRECT_CALL：重定向调用点证据（res.redirect/location 赋值/302 响应）
- EVID_NODE_REDIRECT_TARGET_CONTROL：重定向目标可控性证据
- EVID_NODE_REDIRECT_ALLOWLIST_VALIDATE：目标 allowlist/相对路径校验证据
- EVID_NODE_REDIRECT_ENCODING_BYPASS：编码/协议变体绕过分析证据（`///`、`\`、url-encoded、协议相对）

### CRLF
- EVID_NODE_CRLF_HEADER_WRITE_POINT：Header 写入点证据（setHeader/append/writeHead/cookie 值）
- EVID_NODE_CRLF_PAYLOAD_CONTROL：`\r\n` 可控载荷证据（状态行/头注入）
- EVID_NODE_CRLF_VALIDATE_STRIP：CRLF 过滤/剥离实现证据

### LDAP
- EVID_NODE_LDAP_SEARCH_POINT：LDAP 搜索/绑定调用点证据（ldapjs search/bind）
- EVID_NODE_LDAP_FILTER_CONCAT：filter/DN 拼接证据
- EVID_NODE_LDAP_ESCAPE_IMPLEMENTATION：转义实现证据（filter escape/DN escape，遵循 RFC 4515）
- EVID_NODE_LDAP_BIND_ANONYMOUS_FALLBACK：匿名绑定/fallback 行为证据

### EXPR
- EVID_NODE_EXPR_EVALUATE_POINT：表达式引擎求值调用点证据（expr-eval/mathjs/jexl/jsonata/vm）
- EVID_NODE_EXPR_STRING_CONCAT：表达式串拼接用户输入证据
- EVID_NODE_EXPR_SANDBOX_CONFIG：沙箱/函数白名单配置证据（expr-eval functions 白名单、vm 上下文隔离）

### XPATH
- EVID_NODE_XPATH_SELECT_POINT：XPath 查询调用点证据（xpath.select/libxmljs/xmldom）
- EVID_NODE_XPATH_CONCAT：XPath 表达式拼接证据
- EVID_NODE_XPATH_PARAM_BINDING：参数化/变量绑定防护证据

### SECOND_ORDER
- EVID_NODE_SECOND_ORDER_STORE_POINT：一阶存储点证据（输入进入存储未即时触发）
- EVID_NODE_SECOND_ORDER_TRIGGER_CONTEXT：二阶触发上下文证据（存储值被取出进入危险操作）
- EVID_NODE_SECOND_ORDER_STORAGE_TYPE：存储类型证据（DB/缓存/文件/会话）
- EVID_NODE_SECOND_ORDER_ENCODE_MISMATCH：存储与使用两阶段编码不一致证据

### DESYNC（HTTP 请求走私）
- EVID_NODE_DESYNC_FRONTEND_VARIANT：前端/后端对 CL-TE 处理差异证据（代理/容器/Node http 解析器）
- EVID_NODE_DESYNC_SMUGGLE_PRIMITIVE：走私原语证据（重复/歧义 Content-Length、Transfer-Encoding 混用）
- EVID_NODE_DESYNC_PROXY_CHAIN：中间链路证据（反向代理/负载均衡/Node rawHeaders 处理）
- EVID_NODE_DESYNC_HEADER_CONTROL：header 规范化与重传控制证据

### FS（文件系统综合面）
- EVID_NODE_FS_OPERATION_POINT：文件系统操作调用点证据（fs 全族/path 处理）
- EVID_NODE_FS_PATH_JOIN_CONTROL：path.join/resolve 用户输入参与证据
- EVID_NODE_FS_SYMLINK_FOLLOW：符号链接跟随行为证据（lstat/stat 校验）
- EVID_NODE_FS_PERMISSION_SCOPE：运行时文件权限与目录范围证据

### DOM_XSS
- EVID_NODE_DOM_SINK_POINT：DOM sink 调用点证据（innerHTML/outerHTML/document.write/eval/location）
- EVID_NODE_DOM_SOURCE_TRACE：DOM source 到 sink 流动证据（location.hash/search/referrer/postMessage/name）
- EVID_NODE_DOM_FRAMEWORK_SAFE_API：框架安全 API 使用证据（textContent/createElement/避免 v-html）
- EVID_NODE_DOM_URL_PARAM_SINK：URL 参数直接进 sink 证据（postMessage origin 校验缺失）

### SUPPLY（供应链）
- EVID_NODE_SUPPLY_TOOL_OUTPUT：供应链工具扫描原始输出证据（npm audit --json / osv-scanner）

### EXPORT（电子表格公式注入）

- EVID_NODE_EXPORT_FIELD_USER_CONTROLLED：导出字段来自用户控制数据的证据（req.body/query 进入导出数据）
- EVID_NODE_EXPORT_FORMULA_SINK：导出生成/单元格写入点证据（exceljs/csv-stringify/手写 CSV 写入）
- EVID_NODE_EXPORT_INTERPRETATION_PATH：导出内容会被电子表格解释为公式/命令/链接的路径证据

### PROMPT（AI 提示注入）

- EVID_NODE_PROMPT_UNTRUSTED_CONTENT：不可信内容进入 prompt 上下文的证据
- EVID_NODE_PROMPT_BOUNDARY_CROSSING：不可信内容跨越指令/数据边界的证据
- EVID_NODE_PROMPT_TOOL_PERMISSION_SCOPE：工具/函数调用（含 MCP 工具）权限范围与越权可行性的证据
- EVID_NODE_PROMPT_OUTPUT_HANDLING：LLM 输出被解析、执行或驱动下游动作的处理证据

## 链闭合最小要素（每组 EVID_* 判定证据链闭合时的最小要素清单）

| EVID 分组 | 最小要素（缺一不可） |
| ---- | ---- |
| 注入类（SQL/NOSQL/KQL/XPATH/LDAP） | 可控参数来源 + 拼接点代码 + 边界绕过分析 + 到达执行点路径 |
| CMD/EXPR/TPL/SSTI/DESER | 可控输入 + 执行函数调用 + 逃逸/包装分析 + 执行点可达性 |
| SSRF/HTTP 类 | URL 构造点 + 网络请求调用 + 协议限制分析 |
| FILE/READ/WRITE/UPLOAD/ARCHIVE | 路径构造点 + 文件操作调用 + 规范化/穿越分析 |
| XSS/DOM-XSS/REDIR/CRLF | 输出点 + 编码/转义上下文 + 浏览器端执行路径 |
| AUTH/CSRF/SESS | 鉴权决策点 + 中间件挂载顺序 + 会话/令牌生命周期 |
| CRYPTO/CFG/LOG/LOGIC | 算法/配置/日志写入点 + 弱项证据 + 影响面 |
| SUPPLY（供应链） | CVE 命中 + 版本/来源证据 + 可达性分析（EVID_SUPPLY_*） |
| SECOND_ORDER/DESYNC | 存储与触发双点证据（或链路解析证据）+ 时序/拓扑条件分析 |
| QUERY | 查询执行点 + 用户输入到可执行查询结构的映射 + 查询语义/影响分析 |
| EXPORT | 可控导出字段 + 导出生成 Sink + 电子表格解释与影响证据 |
| PROMPT | 不可信内容证据 + 边界跨越证据 + 工具权限/输出处理影响（仅可控性不得确认） |
