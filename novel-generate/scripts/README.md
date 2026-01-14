# Novel-Generate 脚本说明

本目录包含 AI 小说创作系统的 Python 中间件脚本。

> ⚠️ **注意**: 当前为占位符版本，仅定义接口规范。完整实现需另行开发。

---

## 脚本列表

| 脚本 | 职责 | 依赖 |
|------|------|------|
| `config.py` | 战力锚点、系统常量 | 无 |
| `state_manager.py` | 状态管理（JSON/MySQL/Redis/Neo4j） | pymysql, redis, neo4j |
| `rag_engine.py` | 向量检索（Milvus） | pymilvus, sentence-transformers |

---

## 接口规范

### state_manager.py

```bash
# 获取进度
python state_manager.py --action get_progress

# 获取情绪曲线
python state_manager.py --action get_emo_curve --count 5

# 获取未决悬念
python state_manager.py --action get_hooks

# 初始化角色
python state_manager.py --action init_character --json "{json_data}"

# 更新背包
python state_manager.py --action update_inventory --remove '[...]' --add '[...]'

# 更新关系图
python state_manager.py --action update_graph --changes '[...]'

# 前置校验
python state_manager.py --action preflight --scene_plan "{json}"

# 验证细纲
python state_manager.py --action validate_outline --outline "{json}"

# 保存摘要
python state_manager.py --action save_summary --chapter N --summary "..."

# 更新情绪
python state_manager.py --action update_emo --score N

# 更新悬念
python state_manager.py --action update_hooks --resolved '[...]' --added '[...]'

# 管理员添加物品 (Retcon)
python state_manager.py --action admin_add --target "protagonist" --item "物品名" --note "备注"
```

### rag_engine.py

```bash
# 初始化知识库
python rag_engine.py --action init --source_dir "world_bible/"

# 查询
python rag_engine.py --query "筑基期战斗场景描写" --top_k 3

# 入库新内容
python rag_engine.py --action ingest --text "..." --type "chapter_summary"
```

---

## 返回格式

所有脚本返回 JSON 格式：

**成功**:
```json
{
  "status": "SUCCESS",
  "data": { ... }
}
```

**失败**:
```json
{
  "status": "FAILED",
  "error_code": "E001",
  "message": "物品不存在: 九转金丹"
}
```

---

## 错误码定义

| 错误码 | 含义 |
|--------|------|
| `E001` | 物品不存在 |
| `E002` | 角色已死亡 |
| `E003` | 战力越界 |
| `E004` | 技能未学习 |
| `E005` | 关系矛盾 |
| `E100` | JSON 格式错误 |
| `E101` | 数据库连接失败 |
