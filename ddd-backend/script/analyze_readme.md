# Analyze.py 使用指南

`analyze.py` 是一个专为 Maven/Java 项目设计的智能化日志分析工具，旨在解决日志文件过大导致的查看困难和截断问题。

**核心优势**:
- **防截断设计 (Anti-Truncation)**: 提供交互式搜索模式 (`--grep`)，无需让 AI 读取巨大的原始日志文件。
- **单文件全能**: 集成了路径查找、编码自动检测（支持 GBK/UTF-8）、错误分析和报告生成。
- **环境稳健**: 适配 Windows GBK 环境，自动处理乱码。

## 📁 推荐目录结构

为了保持项目整洁，推荐以下结构（虽然工具支持任意路径）：

```
项目根目录/
├── .business/                        ← 业务逻辑根目录
│   ├── _Global_Protocols/            ← 协议与工具
│   │   └── ddd-backend/
│   │       └── script/
│   │           ├── analyze.py        ← 全能日志分析工具
│   │           └── analyze_readme.md ← 本文档
│   │
│   └── {Feature}/                    ← 功能特性目录 (如: KnowledgeBase)
│       ├── executelogs/              ← [推荐] 存放日志
│       │   ├── Build_Phase2.log
│       │   └── Test_Results.log
│       └── Bug_Report.md             ← [推荐] 报告输出位置
```

## 🚀 核心策略：显式路径

为了保证确定性和安全性，`analyze.py` 采用 **显式路径** 策略。即必须明确指定"输入在哪里"和"输出到哪里"，不进行隐式推断。

命令格式：
```bash
python analyze.py [Input_Log_Path] [Output_Report_Path] [Options]
```

## 🛠️ 使用场景与用法

### 场景 1: 完整错误分析 (Standard Mode)

全量扫描日志，生成包含根本原因分析的 Markdown 报告。

```bash
# 语法: python analyze.py <日志路径> <报告路径>
python analyze.py logs/build.log reports/bug.md
```

### 场景 2: 交互式精准调试 (Interactive Mode) ⭐

当你想查看某个具体的错误上下文，但又不想读取整个文件时，使用搜索模式。结果直接输出到控制台，**绝不会触发 Token 截断**。

```bash
# 搜索 "NullPointer" 并显示前后 10 行
python analyze.py logs/build.log --grep "NullPointer" -c 10
```

### 场景 3: 标准开发场景示例

```bash
python analyze.py \
  .business/KnowledgeBase/executelogs/Build_Error.log \
  .business/KnowledgeBase/Bug_Report.md
```

## ⚙️ 参数详解

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `log_path` | - | (必选) 日志文件路径 | - |
| `report_path` | - | (必选*) 报告输出路径 <br> *注: 使用 --grep 时可选* | - |
| `--grep` | - | 启用搜索模式，指定关键字 | None |
| `--context` | `-c` | 上下文行数 (前后各取 N 行) | 20 |
| `--max-matches` | `-n` | 最大匹配数 (防刷屏) | 10 |

## 📝 输出示例 (Grep 模式)

```text
[*] 正在搜索: 'AsyncDocumentProcessor' (上下文: 5 行, 最大匹配: 10)
------------------------------------------------------------
匹配 #1 (第 108 行):
> [ERROR] .../AsyncDocumentProcessor.java:[108,60] cannot find symbol
  [INFO] 1 error
  [INFO] -------------------------------------------------------------
------------------------------------------------------------
[*] 搜索完成，共找到 1 处匹配
```

## 🛠️ 错误类型支持

工具能够自动识别：Maven 构建失败、Java 编译错误 (符号缺失/类型不匹配)、JUnit 测试失败、运行时异常 (NPE) 等。
