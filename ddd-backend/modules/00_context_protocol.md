# Phase 0: Context Awareness Protocol

**Mission**: 在不阅读全量代码的前提下，通过“外科手术式”扫描建立全知视角，并探测潜在风险。

## 1. ⚓ Feature Anchor (特性锚定)
**Logic**: 必须解决“同一需求，不同表达”的上下文连续性问题。

**Step 1.1: Discovery (扫描现存工作区)**
* **Action**: 执行命令查看已有 Feature。
  `cmd /c "if exist .business dir /b /ad .business"`
* **Analyze**: 
  * 观察输出列表 (e.g., `20240113_UserLogin`, `20240110_OrderFix`).
  * **Semantic Match**: 用户的当前需求是否与列表中的某个目录**语义相关**？
    * *Scenario A*: 用户说“继续写缓存”，列表中有 `20240112_RedisCache` -> **MATCH**.
    * *Scenario B*: 用户说“开发新支付”，列表中无相关项 -> **NO MATCH**.

**Step 1.2: Decision (决策)**
* **CASE A: Match Found (Resume Mode)**
    * **Target**: 使用匹配到的旧目录 (e.g., `20240112_RedisCache`).
    * **Action**: 
        * 读取该目录下的 `01_Design.md` 或 `02_TaskBreakdown.md`。
        * **Report**: "♻️ 识别到现有工作区 `{Matched_Tag}`。准备执行增量扫描..." -> **Continue to Step 2**.
* **CASE B: No Match (New Mode)**
    * **Target**: 生成新标签 `{Date}_{Keyword}` (e.g., `20260114_AliPay`).
    * **Action**: 
        * 创建目录 `mkdir .business/{New_Tag}/executelogs`。
        * **Report**: "🆕 创建新工作区 `{New_Tag}`。" -> **Continue to Step 2**.

## 2. 🧬 Global DNA Scan (全局基因扫描)
**Logic**: 搞清楚项目用什么积木搭成，防止技术栈冲突。严禁猜测，必须基于文件证据。

* **2.1 Dependency Scan** (`pom.xml` / `build.gradle`):
    * **Core**: Spring Boot Version?
    * **Persistence**: MyBatis / MyBatis-Plus / JPA / Hibernate?
    * **Serialization**: Jackson / Fastjson / Gson?
    * **Utils**: Lombok? MapStruct? Hutool?
    * **Test**: JUnit 4/5? Mockito? Spock?
* **2.2 Configuration Scan** (`application.yml` / `.properties`):
    * **DB**: MySQL? PostgreSQL? Connection string pattern?
    * **Cache**: Redis configured?
    * **Server**: Port? Context Path?
    * **Profiles**: dev/test/prod?

## 3. 🏗️ Architecture & Infra Validation (架构与基建验证)
**Logic**: 确认项目骨架是否健康，是否符合 DDD 规范。

* **3.1 DDD Structure Check**:
    * 扫描 `src/main/java` 下的包结构:
    * ✅ `interfaces`: 是否存在? (Web/RPC 入口)
    * ✅ `application`: 是否存在? (Service/Command/Query)
    * ✅ `domain`: 是否存在? (Entity/ValueObject/Aggregate)
    * ✅ `infrastructure`: 是否存在? (Persistence/Gateway Impl)
* **3.2 Infrastructure Components**:
    * **Global Exception**: 搜索 `@ControllerAdvice`。
    * **Response Wrapper**: 搜索 `Result<T>` 或 `Response<T>`。
    * **Auth**: 搜索 `Interceptor` 或 `Filter` 确认鉴权机制。
    * **Utils**: 确认 `infra/utils` 用于防重复造轮子 (DateUtil, RedisUtil)。

## 4. 🎯 Domain Scouting (领域侦查)
**Logic**: 根据需求关键词，寻找切入点。不要通读代码，只看骨架。

* **4.1 Existing APIs**:
    * 搜索 `@RestController` / `@RequestMapping`，列出关键端点。
* **4.2 Data Models**:
    * 搜索 `@TableName` / `@Entity`，确认现有数据库表映射。
* **4.3 Database Status**:
    * 检查 `resources/db` 是否有迁移脚本 (Flyway/Liquibase)?
    * **检测激活的 Profile**:
      * 读取 `application.yml` 中的 `spring.profiles.active` 值
      * 或检查启动命令/环境变量中指定的 profile
      * 如无法确定，询问用户当前使用的环境
    * **使用 db_inspector.py 获取实时表结构**:
      ```bash
      # 从项目根目录执行
      python .business/_Global_Protocols/ddd-backend/script/db_inspector.py \
          --host {DB_HOST} \
          --user {DB_USER} \
          --password {DB_PASS} \
          --database {DB_NAME} \
          -o .business/{Feature}/DB_Schema.md
      ```
    * 如果脚本执行失败（数据库不可达），询问用户数据库状态。

## 5. ⚠️ Gap Analysis (落差分析)
**Logic**: 用户的欲望 vs 现有的能力。

* **Action**: 将“用户需求关键词”与 Step 2 & 3 的扫描结果进行比对。
* **Trigger Warning**:
    * 如果用户要 "Kafka" 但 `pom.xml` 无依赖 -> 🚨 **WARN**.
    * 如果用户要 "需鉴权接口" 但未发现 Auth 机制 -> 🚨 **WARN**.
    * 如果用户要 "新增表" 但未发现 DB 迁移工具 -> 💡 **TIP**.

