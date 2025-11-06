#### 1. 整体设计原则
- **架构基础**：采用Spring Boot框架构建RESTful API后端，确保轻量级、易扩展。模块独立成一个Controller（ModelController）和Service（ModelService），遵循MVC模式。Controller负责HTTP接口处理，Service处理核心业务逻辑（如文件扫描、切换逻辑）。使用Lombok简化实体类和日志。
- **存储策略**：不引入数据库（如MySQL），而是文件系统存储。模型文件统一保存在项目根目录下的`/models/`文件夹中：
  - 每个模型作为一个子目录（e.g., `/models/CNN-Enhanced/`），包含：
    - 核心模型文件：`model.pkl`（Python pickle格式的CNN模型）。
    - 元数据文件：`metadata.json`（JSON格式存储：{"id": "uuid", "name": "CNN-Enhanced", "user": "admin1", "trainTime": "2025-11-03T10:00:00", "accuracy": 0.95, "version": "v1.0", "trainDate": "2025-11-03"}）。
  - 活跃模型标记：一个全局配置文件`/models/active.json`（{"activeModel": "CNN-Enhanced"}），用于标识当前生效模型。
  - 优点：简单、无外部依赖、易备份/迁移。缺点：并发高时扫描可能慢（后续可加缓存如Redis），但当前场景（管理员操作）并发低，可接受。
- **与Python端交互**：通过HTTP调用Python服务器（假设Python端暴露REST API，如`/api/switch_model`）。当前用空函数（e.g., `notifyPythonSwitch(modelName)`）占位，实际实现时替换为`RestTemplate`或`WebClient`发送POST请求。Python端收到后加载新模型到内存，用于推理。
- **错误处理与安全性**：
  - 统一返回格式：成功用200 + JSON msg，失败用4xx/5xx + 错误msg（e.g., {"error": "模型不存在"}）。
  - 认证：假设所有接口需JWT token（管理员角色），用Spring Security拦截。
  - 异常：文件IO异常用try-catch，日志用SLF4J记录。
- **性能考虑**：扫描目录用`Files.walk()`，限制深度1层。活跃状态在扫描时从`active.json`读取并注入列表。
- **测试友好**：Service方法纯函数化，便于单元测试（Mock文件系统用TempDir）。

#### 2. 核心功能设计
模块对应三个接口，逻辑如下：

- **功能1: 获取模型列表（GET /api/models）**
  - **触发场景**：前端页面加载时调用，显示模型表格。
  - **业务逻辑**：
    1. Service扫描`/models/`目录，遍历每个子目录。
    2. 对于每个子目录，读取`metadata.json`，解析成ModelEntity（POJO：id, name, user, trainTime, accuracy, version, trainDate）。
    3. 读取`/models/active.json`，获取activeModelName，将匹配的模型的`active`字段设为true（其他false）。
    4. 排序列表：按trainDate降序（最新训练优先）。
    5. 如果目录为空，返回空列表[]；如果active.json缺失/无效，默认为null active。
  - **与前端交互**：返回JSON数组`[{ "id": "uuid1", "name": "CNN-Base", "user": "admin1", "trainTime": "PT2H30M", "accuracy": 0.92, "version": "v1.0", "trainDate": "2025-11-03", "active": true }]`. 前端解析后渲染表格，支持排序/过滤。
  - **边界**：目录不存在时创建；JSON解析失败跳过该模型，日志警告。
  - **Python端交互**：无，直接文件读取。

- **功能2: 切换当前模型（POST /api/models/apply）**
  - **触发场景**：管理员在列表中点击“切换”按钮，提交modelName。
  - **业务逻辑**：
    1. 从请求体提取modelName，验证是否存在（先调用获取列表逻辑，检查name匹配）。
    2. 如果不存在，返回400 {"error": "模型不存在"}。
    3. 更新`/models/active.json`：{"activeModel": modelName}，原子写（用FileLock避免并发）。
    4. 调用空函数`notifyPythonSwitch(modelName)`（占位：实际发送POST到Python端`/api/switch_model`，body={"model": modelName}，Python端重载模型到全局变量）。
    5. 通知成功，返回200 {"msg": "模型已切换"}。
  - **与前端交互**：前端提交后，轮询或WebSocket刷新列表，更新active图标（e.g., 绿色标签）。如果切换失败，前端弹窗重试。
  - **边界**：只能切换已训练模型；切换后立即生效（Python端同步<1s）。日志记录切换事件。
  - **Python端交互**：空函数模拟通知，Python端响应确认（e.g., "switched"）。

- **功能3: 删除模型（DELETE /api/models/{modelName}）**
  - **触发场景**：管理员在列表中点击“删除”按钮，确认后调用。
  - **业务逻辑**：
    1. 从路径提取modelName，验证存在且非active（先检查active.json）。
    2. 如果是active，返回409 {"error": "活跃模型不可删除，请先切换"}。
    3. 如果不存在，返回404 {"error": "模型不存在"}。
    4. 删除整个子目录`/models/{modelName}/`（递归删除，用`Files.walk().forEach(p -> p.toFile().delete())`）。
    5. 如果删除后active模型被删（异常情况），重置active.json为空。
    6. 返回200 {"msg": "模型删除成功"}。
  - **与前端交互**：前端二次确认弹窗，成功后刷新列表（移除行）。批量删除可后续扩展，但当前单条。
  - **边界**：删除前备份元数据（可选日志）；IO失败重试3次。
  - **Python端交互**：无（删除不影响运行中模型，除非是active，但已禁止）。

#### 3. 模块间依赖与扩展性
- **依赖**：Spring Web、Jackson（JSON）、Apache Commons IO（文件操作）。无外部服务依赖（Python调用异步，非阻塞）。
- **与其它模块集成**：
  - 训练模块：训练完成后，Service自动创建新模型目录+metadata.json，并可选设为active。
  - 用户模块：user字段从登录上下文获取（e.g., SecurityContextHolder）。
  - 统计模块：准确率可从metadata拉取，供报表用。
- **扩展点**：
  - 加缓存：用@Cacheable注解扫描结果，TTL 5min。
  - 搜索/分页：GET加query param ?page=1&search=enhanced，返回分页列表。
  - 模型上传：未来POST /api/models/upload，支持从外部导入。
- **潜在风险与缓解**：
  - 文件并发：管理员单用户，风险低；加锁。
  - 路径安全：用Path.normalize()防路径注入。
  - 准确率更新：训练后动态刷新metadata。

