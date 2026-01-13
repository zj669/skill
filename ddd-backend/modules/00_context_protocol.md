# Phase 0: Context Awareness Protocol

**Mission**: 在不阅读全量代码的前提下，通过“外科手术式”扫描建立全知视角，并探测潜在风险。

## 1. ⚓ Feature Anchor
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
        * **Report**: "♻️ 识别到现有工作区 `{Matched_Tag}`。上下文已自动恢复。" -> **GOTO Step 5**.
* **CASE B: No Match (New Mode)**
    * **Target**: 生成新标签 `{Date}_{Keyword}` (e.g., `20260114_AliPay`).
    * **Action**: 
        * 创建目录 `mkdir .business/{New_Tag}/executelogs`。
        * **Report**: "🆕 创建新工作区 `{New_Tag}`。" -> **Continue to Step 2**.

## 2. 🧬 Global DNA Scan
**Logic**: 搞清楚项目用什么积木搭成，防止技术栈冲突。严禁猜测，必须基于文件证据。
*(仅当 Step 1.2 为 CASE B 时执行)*

* **Manifest Scan** (`pom.xml` / `build.gradle`):
    * **ORM**: MyBatis / MyBatis-Plus / JPA / Hibernate?
    * **JSON**: Jackson / Fastjson / Gson?
    * **Utils**: Lombok? MapStruct? Hutool?
* **Structure Scan**:
    * **Base Package**: 扫描 `src/main/java` 确认根包名 (e.g., `com.antigravity.core`).
    * **Wheel Check (防重复)**: 扫描 `infra/utils` 或 `common`。确认是否已有 `DateUtil`, `RedisUtil`, `Result<T>`。**严禁重复造轮子。**

## 3. ⚠️ Gap Analysis 
**Logic**: 用户的欲望 vs 现有的能力。
*(仅当 Step 1.2 为 CASE B 时执行)*

* **Action**: 将“用户需求关键词”与 Step 2 扫描到的“依赖列表”进行比对。
* **Trigger Warning**:
    * 如果用户要 "Kafka" 但 `pom.xml` 无依赖 -> 🚨 **WARN**.
    * 如果用户要 "Redis" 但 `pom.xml` 无依赖 -> 🚨 **WARN**.
* **Report**: "⚠️ 风险预警: 需求涉及 [组件名]，但未发现相关依赖。需在 Phase 1 规划依赖引入。"

## 4. 🎯 Domain Scouting
**Logic**: 根据需求关键词，寻找切入点。不要通读代码，只看骨架。
*(仅当 Step 1.2 为 CASE B 时执行)*

* **Trace the Link**:
    1.  **Entrance**: 搜索 Controller (URL 风格? Restful?)
    2.  **Model**: 搜索 Entity/DO (贫血还是充血? 用了 `@Data` 吗?)
    3.  **Data**: 搜索 Mapper/Repository (XML 还是 Annotation?)
