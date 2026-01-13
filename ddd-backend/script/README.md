# 日志分析工具使用指南

## 📖 简介

`log_analyzer.py` 是一个专门用于分析 Maven/Java 项目构建和测试日志的 Python 工具。它解决了 PowerShell 命令输出被截断的问题，能够精确定位错误位置并生成结构化的分析报告。

## ✨ 主要特性

- ✅ **精确错误提取**: 自动识别 `[ERROR]`、`FAILURE`、`Exception` 等错误模式
- ✅ **堆栈跟踪分析**: 提取完整的异常堆栈信息
- ✅ **避免输出截断**: 将结果保存到文件，不受终端宽度限制
- ✅ **智能错误分析**: 自动识别常见错误类型（符号未找到、包缺失等）
- ✅ **灵活配置**: 支持自定义错误数量、上下文行数等参数
- ✅ **多种报告格式**: 支持详细报告和简洁的 Bug 报告

## 🚀 快速开始

### 基本用法

```bash
# 分析日志并输出到控制台
python script/log_analyzer.py -l .business/feature-name/executelogs/build.log

# 生成完整报告并保存到文件
python script/log_analyzer.py -l .business/feature-name/executelogs/build.log -o .business/feature-name/Error_Analysis.md

# 生成简洁的 Bug 报告（符合文档格式）
python script/log_analyzer.py -l .business/feature-name/executelogs/build.log --bug-report -o .business/feature-name/Bug_Report.md
```

### 高级用法

```bash
# 提取更多错误（前 10 个）
python script/log_analyzer.py -l path/to/build.log -m 10

# 增加上下文行数（每个错误后 30 行）
python script/log_analyzer.py -l path/to/build.log -c 30

# 如果没有找到错误，显示文件末尾 50 行
python script/log_analyzer.py -l path/to/build.log --tail 50
```

## 📋 命令行参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--log` | `-l` | 日志文件路径（必需） | - |
| `--output` | `-o` | 报告输出路径（可选） | - |
| `--max-errors` | `-m` | 最多提取的错误数量 | 5 |
| `--context-lines` | `-c` | 每个错误的上下文行数 | 20 |
| `--bug-report` | - | 生成简洁的 Bug 报告格式 | False |
| `--tail` | - | 未找到错误时读取文件末尾指定行数 | - |

## 📊 输出示例

### 详细报告格式

```
================================================================================
错误日志分析报告
日志文件: .business/user-auth/executelogs/build.log
分析时间: 2026-01-14 00:00:00
发现错误: 3 个
================================================================================

## 错误 #1: ERROR
位置: 第 125 行
--------------------------------------------------------------------------------
### 错误内容:
[ERROR] /C:/java/skill/src/OrderService.java:[15,20] cannot find symbol

### 堆栈跟踪:
  symbol:   class Money
  location: class com.example.OrderService

### 上下文 (后续 10 行):
[ERROR]   symbol:   class Money
[ERROR]   location: class com.example.OrderService
[ERROR] Failed to execute goal...

### 错误分析:
❌ 类型: 符号未找到（编译错误）
   缺失符号: class Money
📍 位置: OrderService.java
   行列: [15, 20]

================================================================================
```

### Bug 报告格式

```markdown
> **[Bug Report]**
> * **Failure Type**: SymbolNotFound
> * **Location**: OrderService.java:[15,20]
> * **Key Trace**:
> ```text
[ERROR] /C:/java/skill/src/OrderService.java:[15,20] cannot find symbol
[ERROR]   symbol:   class Money
[ERROR]   location: class com.example.OrderService
> ```
> * **Root Cause**: 缺少类或包的导入，或者类名拼写错误
```

## 🔧 集成到调试流程

### 替代原有的 PowerShell 命令

**原流程**（第 5 阶段文档）:
```powershell
Get-Content -Path "LOG_PATH" -Encoding UTF8 | Select-String -Pattern "\[ERROR\]|Caused by|FAILURE" -Context 0,20 | Select-Object -First 5 | Out-String -Width 4096
```

**新流程**:
```bash
python script/log_analyzer.py -l "LOG_PATH" -o .business/{Feature}/Error_Analysis.md --bug-report
```

### 优势对比

| 特性 | PowerShell 命令 | Python 工具 |
|------|----------------|------------|
| 输出截断 | ❌ 容易被截断 | ✅ 不会截断 |
| 错误分析 | ❌ 无 | ✅ 智能分析 |
| 保存报告 | ❌ 需额外重定向 | ✅ 内置支持 |
| 可读性 | ⚠️ 一般 | ✅ 结构化报告 |
| 可定制性 | ⚠️ 有限 | ✅ 高度灵活 |

## 🎯 典型使用场景

### 场景 1: 编译失败诊断

```bash
# 构建失败后立即分析
mvn clean install > .business/feature/executelogs/build.log 2>&1
python script/log_analyzer.py -l .business/feature/executelogs/build.log --bug-report
```

### 场景 2: 测试失败分析

```bash
# 测试失败后生成详细报告
mvn test > .business/feature/executelogs/test.log 2>&1
python script/log_analyzer.py -l .business/feature/executelogs/test.log -o .business/feature/Test_Analysis.md
```

### 场景 3: 批量日志分析

```powershell
# 分析多个日志文件
Get-ChildItem .business/*/executelogs/*.log | ForEach-Object {
    python script/log_analyzer.py -l $_.FullName -o "$($_.DirectoryName)\Analysis_$($_.Name).md"
}
```

## 🐛 常见问题

### Q: 脚本提示 "FileNotFoundError"
**A**: 检查日志文件路径是否正确，确保文件存在。

### Q: 没有找到任何错误
**A**: 使用 `--tail` 参数查看文件末尾内容，可能错误信息在文件末尾：
```bash
python script/log_analyzer.py -l path/to/build.log --tail 50
```

### Q: 想要更详细的堆栈信息
**A**: 增加 `--context-lines` 参数：
```bash
python script/log_analyzer.py -l path/to/build.log -c 50
```

## 📝 扩展建议

如果需要自定义错误模式或分析逻辑，可以修改 `log_analyzer.py` 中的：

1. **ERROR_PATTERNS**: 添加新的错误匹配模式
2. **_analyze_error()**: 增强错误分析逻辑
3. **_infer_root_cause()**: 改进根本原因推断

## 📚 相关文档

- [05_debugging_protocol.md](../modules/05_debugging_protocol.md) - 调试协议文档
