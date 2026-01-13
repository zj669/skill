# Phase X: Debugging & Recovery Protocol

**Tech Lead 指令**: 停止无效的循环读取！我们不需要看完整的日志，只需要看**第一个致命错误**。

## 🛑 Circuit Breaker (熔断机制)
**Rule**: 针对同一个 Log 文件，**严禁**执行超过 1 次读取命令。
* **One Shot**: 必须使用下方定义的“精确打击”命令，一次性获取所需信息。
* **Stop**: 如果命令返回为空或无意义信息，**立即停止**并请求人工介入，严禁尝试使用 `type`、`cat` 或复杂的正则去重读文件。

## 1. 🔍 Diagnosis Protocol (诊断步骤)

**Data Source**: `.business/{Feature}/executelogs/` 下的目标日志文件。

### Step 1: Precision Strike (精确打击 - 强制执行)

**Rationale**: Maven/Java 的错误往往是级联的。修复前 5 个错误通常能解决 90% 的问题。
**Command (PowerShell Optimized)**:
请直接执行以下命令（不要修改参数）：

```powershell
Get-Content -Path "LOG_PATH" -Encoding UTF8 | Select-String -Pattern "\[ERROR\]|Caused by|FAILURE" -Context 0,20 | Select-Object -First 5 | Out-String -Width 4096

```

* **原理解析**:
* `Select-String -Pattern ...`: 同时捕获编译错误(`[ERROR]`)、构建失败(`FAILURE`)和运行时异常(`Caused by`)。
* `-Context 0,20`: **核心**。对于每一行错误，自动抓取其后 **20行**（即堆栈详情）。
* `Select-Object -First 5`: **防刷屏**。只看前 5 个错误，防止 Token 溢出或日志过长被截断。
* `Out-String -Width 4096`: **防截断**。强制扩展 PowerShell 的行宽，防止 Java 长类名被切断。



### Step 2: Fallback (备选策略 - 仅当 Step 1 输出为空时)

如果 Step 1 真的什么都没抓到（罕见情况，如 JVM 崩溃），则读取文件末尾的摘要：

```powershell
Get-Content -Path "LOG_PATH" -Encoding UTF8 -Tail 50 | Out-String -Width 4096

```

### Step 3: Analysis Report (必填)

根据 Step 1 输出的片段，填写报告：

> **[Bug Report]**
> * **Failure Type**: (e.g., `SymbolNotFound`, `CompilationError`)
> * **Location**: (e.g., `OrderService.java:[15,20]`)
> * **Key Trace**:
> ```text
> [ERROR] /C:/.../OrderService.java:[15,20] cannot find symbol
> [ERROR]   symbol:   class Money
> 
> ```
>
>
> * **Root Cause**: (一句话解释原因)
>
>

## 2. 🛠️ Fix Strategy (修复策略)

**Option A: Code Fix (代码逻辑错误)**

* 展示 `diff`。
* 解释为什么之前的逻辑会导致这个 Bug。

**Option B: Config Fix (配置/环境错误)**

* 检查 `application.yml` 或 `pom.xml`。
* 常见坑点：`@MapperScan` 路径不对、Lombok 版本冲突、JDK 版本不一致。

**Option C: Test Fix (测试用例错误)**

* 如果业务代码是对的，是测试数据造得不对（例如 Mock 了一个空对象），修正测试代码。

---

## 3. 🔄 Verification (回归验证)

修复后，仅重跑刚才失败的那个测试。
**Command**: `cmd /c "chcp 65001 >nul && mvn test -Dtest={FixedClass} > .business/{Feature}/executelogs/Retry_Fix.log 2>&1"`

---

## 📂 Traceability

将本次排查报告追加保存至: `.business/{Feature}/Bug_Analysis.md`
