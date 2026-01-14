# 数据库结构检查工具 (Database Inspector)

`db_inspector.py` 是一个轻量级的数据库文档生成工具，用于导出当前数据库的表结构、字段定义和 DDL。

**核心设计**:
- **显式连接 (Explicit Connection)**: 强制要求提供主机、用户名、密码等参数，拒绝隐式读取配置文件，确保连接的可控性和安全性。
- **标准化报告**: 生成包含表概览、字段详情和 DDL 的 Markdown 报告。

## 🚀 快速开始

### 基础用法 (打印到控制台)

```bash
python db_inspector.py \
  --host localhost \
  --port 3306 \
  --user root \
  --password 123456 \
  --database mydb
```

### 生成文档 (保存到文件)

```bash
python db_inspector.py \
  --host 192.168.1.100 \
  --user admin \
  --password secret \
  --database production_db \
  -o ./docs/db_schema.md
```

## ⚙️ 参数详解

| 参数 | 说明 | 必选 | 默认值 |
|------|------|------|--------|
| `--host` | 数据库主机 IP 或域名 | ✅ | - |
| `--user` | 数据库用户名 | ✅ | - |
| `--password` | 数据库密码 | ✅ | - |
| `--database` | 目标数据库名称 | ✅ | - |
| `--port` | 数据库端口 | ❌ | 3306 |
| `-o`, `--output` | 报告输出路径 (如不指定则打印到控制台) | ❌ | - |

## 📦 依赖说明

工具依赖 `pymysql`。如果运行报错，请安装：

```bash
pip install pymysql
```
