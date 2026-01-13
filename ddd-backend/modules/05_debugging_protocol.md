# Phase X: Debugging & Recovery Protocol

**Trigger**: 编译失败、测试红灯 (Exit Code != 0) 或用户反馈 "Bug"。

## 🛑 Circuit Breaker 
**Rule**: 针对同一个错误，**严禁重跑命令**来复现。
1.  **Read Once**: 只允许读取一次生成的 Log 文件。
2.  **Stop If Unknown**: 如果在日志中找不到明显报错，**立即停止**并告知用户，严禁尝试去读取 `target/` 下的其他无关文件。

## 1. 🔍 Diagnosis Protocol 

**Data Source**: 仅分析 `.business/{Feature}/executlogs/` 下的目标日志文件。

### Step 1: Smart Retrieval Strategy 

**Tech Lead Warning**: 严禁使用简单的 `Select-String`，这会丢失堆栈信息。请根据错误类型选择策略：

**Encoding Note**: 日志文件已强制为 UTF-8 编码。读取时请显式指定 `-Encoding UTF8` (针对 PowerShell 5.1) 或依赖默认 (PowerShell Core 7+)。为兼容性建议加上。

#### 🟢 Strategy A: Check the Tail
Maven/Gradle 的 "Build Failure" 汇总通常在文件末尾。
* **Command**: `Get-Content -Path "LogPath" -Tail 50 -Encoding UTF8`
* **Target**: 快速定位是哪个 Module 编译失败，或哪个 Test Case 挂了。

#### 🟡 Strategy B: Context Search
如果 Tail 没找到细节，必须搜索关键词并**抓取上下文**。
* **Command**: 
    `Select-String -Path "LogPath" -Pattern "\[ERROR\]|Caused by|Exception|FAILURE" -Context 2, 50 -Encoding UTF8`
* **Key Parameter**: `-Context 2, 50`
    * **含义**: 抓取匹配行的**前 2 行** (看是用在哪个类) 和**后 50 行** (看完整的 Stack Trace)。
    * **Benefit**: 一次性抓取完整堆栈，拒绝“盲人摸象”。

### Step 2: Extract & Report

### 🐞 Bug Analysis Report
* **Log File**: `.business/{Feature}/executlogs/xxxx.log`
* **Failure Type**: [e.g., `NullPointerException`, `CompilationError`]
* **Key Stack Trace**: 
    ```text
    (粘贴 Strategy B 抓取到的核心堆栈，包含 Caused by 部分)
    ```
* **Root Cause**: 
    * [ ] **Syntax/Compile**: 语法错误 (e.g., Symbol not found, semi-colon missing)
    * [ ] **Logic/Assertion**: 业务逻辑错误 (预期值与实际值不符)
    * [ ] **Configuration**: 环境/Bean错误 (e.g., NoSuchBeanDefinition, Maven profile issue)
    * [ ] **Dependency**: 版本冲突或 Jar 包缺失

## 2. 🛠️ Fix Strategy 

根据 Root Cause 选择策略（必须解释原因）：

* **Strategy A (Code Fix)**: 修改 Java 代码逻辑。
    * *Requirement*: 必须展示修改前后的 `diff` 对比。
* **Strategy B (Config Fix)**: 修改 `application.yml` 或注解。
    * *Check*: 检查 `@MapperScan`, `@ComponentScan` 路径是否正确？配置文件是否生效？
* **Strategy C (Test Fix)**: 如果业务代码逻辑正确，是测试用例写错了（如 Mock 数据不对）。
    * *Action*: 修正测试代码。

## 3. 🧪 Regression Check 
* **Action**: 修复后，建议仅重新运行**刚才失败的那个 Task**。
    * *Command*: `cmd /c "mvn test -Dtest=FixedClass > .business/{Feature}/executlogs/Retry_..."`

---

## 📂 Traceability 
将本次排查报告追加保存至: `.business/{Feature}/Bug_Analysis.md`