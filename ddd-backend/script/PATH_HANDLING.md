# 路径处理增强 - 使用指南

## 📁 项目结构

```
项目根目录/
├── .business/
│   ├── _Global_Protocols/
│   │   └── ddd-backend/
│   │       └── script/
│   │           ├── log_analyzer.py      ← 核心分析工具
│   │           ├── analyze.py           ← Python 快捷脚本 ⭐ 新增
│   │           └── analyze.ps1          ← PowerShell 快捷脚本 ⭐ 新增
│   │
│   ├── Konwledage/                      ← Feature 目录（名称会变化）
│   │   ├── executelogs/
│   │   │   ├── Build_Phase2_*.log
│   │   │   └── Test_*.log
│   │   └── Bug_Report.md                ← 自动生成的报告
│   │
│   ├── UserAuthentication/             ← 另一个 Feature
│   │   └── ...
│   └── OrderManagement/                ← 又一个 Feature
│       └── ...
```

---

## 🚀 使用方法

### 方案 1：使用快捷脚本（推荐）⭐

#### Python 版本

```bash
# 基本用法：自动分析最新日志
cd .business/_Global_Protocols/ddd-backend/script
python analyze.py Konwledage

# 指定日志文件
python analyze.py Konwledage Build_Phase2_UTF8_20260114002053.log
```

#### PowerShell 版本

```powershell
# 基本用法：自动分析最新日志
cd .business/_Global_Protocols/ddd-backend/script
.\analyze.ps1 Konwledage

# 指定日志文件
.\analyze.ps1 Konwledage Build_Phase2_UTF8_20260114002053.log

# 或者使用完整参数名
.\analyze.ps1 -FeatureName Konwledage -LogFileName Build_Phase2_UTF8_20260114002053.log
```

### 方案 2：直接使用 log_analyzer.py

```bash
# 从项目根目录执行
python .business/_Global_Protocols/ddd-backend/script/log_analyzer.py \
    -l .business/Konwledage/executelogs/Build_Phase2_UTF8_20260114002053.log \
    -o .business/Konwledage/Bug_Report.md \
    --bug-report
```

---

## ✨ 快捷脚本的优势

| 特性 | 直接使用 log_analyzer.py | 使用快捷脚本 |
|-----|-------------------------|------------|
| **路径输入** | 需要完整路径 | 只需 Feature 名称 |
| **日志选择** | 手动指定文件名 | 自动选择最新日志 ⭐ |
| **输出位置** | 手动指定路径 | 自动保存到 Feature 目录 ⭐ |
| **错误提示** | 基本 | 详细的目录检查 ⭐ |
| **易用性** | ⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 📊 输出示例

### 使用快捷脚本

```
$ python analyze.py Konwledage
============================================================
🔧 日志分析工具
============================================================
Feature: Konwledage
日志文件: Konwledage/executelogs/Build_Phase2_UTF8_20260114002053.log
报告输出: Konwledage/Bug_Report.md
============================================================

🔍 正在分析日志: .business\Konwledage\executelogs\Build_Phase2_UTF8_20260114002053.log
📝 检测到编码: GBK (置信度: 89%)
✅ 发现 3 个错误

✅ 报告已保存到: .business\Konwledage\Bug_Report.md

============================================================
✅ 分析完成！
📊 报告位置: .business\Konwledage\Bug_Report.md
============================================================
```

---

## 🔧 工作原理

### 快捷脚本的路径计算

```python
# 1. 获取脚本所在目录
script_dir = Path(__file__).parent
# 结果: .business/_Global_Protocols/ddd-backend/script

# 2. 向上查找 .business 目录（3 层）
business_dir = script_dir.parent.parent.parent
# 结果: .business

# 3. 构建 Feature 目录路径
feature_dir = business_dir / feature_name
# 结果: .business/Konwledage

# 4. 自动查找最新日志
log_files = list(executelogs_dir.glob("*.log"))
log_file = max(log_files, key=lambda p: p.stat().st_mtime)
```

---

## 📝 实际使用场景

### 场景 1：快速分析当前 Feature

```bash
# 不记得具体日志文件名
cd .business/_Global_Protocols/ddd-backend/script
python analyze.py UserAuthentication
# ✅ 自动找到最新日志并分析
```

### 场景 2：分析特定的历史日志

```bash
# 需要查看某个特定的构建
python analyze.py OrderManagement Build_Phase1_20260113_153022.log
```

### 场景 3：批量分析多个 Feature

```powershell
# PowerShell 批量处理
$features = @("UserAuth", "OrderMgmt", "Payment")
foreach ($feature in $features) {
    Write-Host "分析 $feature..."
    .\analyze.ps1 $feature
}
```

---

## ⚙️ 高级设置

### 自定义输出文件名

如果需要不同的输出文件名，可以修改 `analyze.py` 第 68 行：

```python
# 原代码
report_file = feature_dir / "Bug_Report.md"

# 修改为包含时间戳
from datetime import datetime
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
report_file = feature_dir / f"Bug_Report_{timestamp}.md"
```

### 添加更多参数

可以在快捷脚本中添加更多 log_analyzer.py 的参数：

```python
cmd = [
    "python",
    str(log_analyzer),
    "-l", str(log_file),
    "-o", str(report_file),
    "--bug-report",
    "-m", "10",           # 新增：最多 10 个错误
    "-c", "30",           # 新增：30 行上下文
    "-e", "gbk"           # 新增：指定编码
]
```

---

## 🐛 故障排除

### 问题 1：找不到 Feature 目录

**错误**：
```
❌ 错误：Feature 目录不存在: .business\Konwledage
```

**解决**：
1. 检查 Feature 名称拼写是否正确
2. 确认目录确实存在：`ls .business`

### 问题 2：未找到日志文件

**错误**：
```
❌ 错误：未在 .business\Konwledage\executelogs 找到日志文件
```

**解决**：
1. 检查 executelogs 目录是否存在
2. 确认目录中有 .log 文件
3. 手动指定日志文件名

### 问题 3：脚本路径问题

**错误**：
```
❌ Python 找不到模块
```

**解决**：
- 确保在 `script` 目录下执行脚本
- 或使用绝对路径

---

## 📚 相关文档

- [log_analyzer.py 使用指南](./README.md)
- [调试协议文档](../modules/05_debugging_protocol.md)
- [编码检测功能说明](encoding_enhancement_report.md)

---

## 💡 最佳实践

1. **使用快捷脚本**：大多数情况下，快捷脚本已经足够
2. **Feature 名称规范**：使用驼峰命名或下划线分隔
3. **日志文件命名**：建议包含时间戳和阶段信息
4. **定期清理**：删除旧的日志和报告文件

---

## 🎯 总结

通过快捷脚本，您可以：
- ✅ 简化命令：从复杂的路径变成一个 Feature 名称
- ✅ 自动化：自动找到最新日志
- ✅ 标准化：统一的输出位置
- ✅ 易维护：脚本处理所有路径逻辑
