# Phase 3: 数据结算协议 (Data Manager Protocol)

## 📌 目标
将定稿正文中的事件提取出来，更新所有相关数据库，完成数据闭环。

---

## 🎭 Sub-Skill: Data_Manager

**角色定位**: 你是数据管理员，负责将"发生的事情"同步到系统记忆中。

**核心职责**:
1. 解析正文，提取结构化事件
2. 更新角色状态 (JSON)
3. 更新人物关系 (Neo4j)
4. 更新剧情记忆 (MySQL + Milvus)
5. 更新体验曲线 (Redis)

---

## 🛠 执行步骤

### Step 1: 事件提取

**读取草稿末尾的元数据**:
```markdown
[ITEMS_USED]: ["青锋剑", "灵力恢复丹"]
[ITEMS_GAINED]: ["王家令牌"]
[RELATIONS_CHANGED]: [{"target": "王虎", "change": "DEAD"}]
[EMO_SCORE]: 45
```

**如果元数据不完整，调用 AI 分析**:
```
请分析以下章节正文，提取：
1. 使用了哪些物品
2. 获得了哪些新物品
3. 人物关系发生了什么变化
4. 是否有新的悬念/伏笔
```

---

### Step 2: 状态更新 (JSON)

> [!CAUTION]
> 🔧 **MUST_EXECUTE** - 你必须实际执行此脚本！

**执行命令**:
```bash
python scripts/state_manager.py --action update_inventory \
  --remove '["灵力恢复丹"]' \
  --add '["王家令牌"]'
```

**✅ 执行检查点**: 必须报告更新结果

**更新项目**:
| 字段 | 更新逻辑 |
|------|---------|
| `inventory` | 加减物品 |
| `level` | 突破升级 |
| `spirit_power` | 战斗消耗后回正 |
| `skills` | 新学技能 |

---

### Step 3: 关系更新 (Neo4j)

> [!CAUTION]
> 🔧 **MUST_EXECUTE** - 你必须实际执行此脚本！

**执行命令**:
```bash
python scripts/graph_query.py --action batch_update_relations \
  --changes '[{"from": "叶凡", "to": "王虎", "relation": "KILLED"}]'
```

**关系类型**:
| 类型 | 含义 | 触发条件 |
|------|------|---------|
| KILLED | 击杀 | 正文描写死亡 |
| HATES | 仇恨 | 结仇/冲突 |
| ALLIED | 结盟 | 合作/拜师 |
| OWES | 欠人情 | 被救/受恩 |

---

### Step 4: 记忆存储 (MySQL + Milvus)

**生成章节摘要**:
```
请用 100 字总结本章剧情，重点包含：
- 关键事件
- 人物状态变化
- 新增伏笔
```

**写入 MySQL**:
```bash
python scripts/state_manager.py --action save_summary \
  --chapter {n} --summary "{summary_text}"
```

**写入 Milvus** (向量化):
```bash
python scripts/rag_engine.py --action ingest --text "{summary_text}" --type "chapter_summary"
```

---

### Step 5: 体验曲线更新 (Redis)

**更新爽点记录**:
```bash
python scripts/state_manager.py --action update_emo \
  --score {emo_score}
```

**更新悬念列表**:
```bash
python scripts/state_manager.py --action update_hooks \
  --resolved '["戒指老爷爷"]' \
  --added '["王家复仇计划"]'
```

---

### Step 6: 结算确认

**最终状态检查**:
```bash
python scripts/state_manager.py --action verify_settlement --chapter {n}
```

**返回示例**:
```json
{
  "status": "SUCCESS",
  "changes_summary": {
    "inventory": "+1 王家令牌, -1 灵力恢复丹",
    "relations": "王虎 -> DEAD",
    "hooks": "+1 新悬念, -1 已回收"
  }
}
```

---

## 📄 交付物

| 输出 | 类型 | 用途 |
|------|------|------|
| 更新后的 `protagonist.json` | JSON | 反映最新角色状态 |
| 章节摘要入库 | MySQL + Milvus | 长期记忆 |
| 爽点曲线更新 | Redis | 下一章规划依据 |

## 🛑 Stop Point / 🔄 Auto-Pilot

**Logic**:
1. **Check Auto-Mode**:
   - If `context.auto_mode` is **True**:
     > 🔧 **MUST_EXECUTE** (Sequence)
     > ```bash
     > # 1. 进入下一章
     > python scripts/state_manager.py --action next_chapter
     > # 2. 流转回章纲阶段
     > python scripts/state_manager.py --action update_step --status NEED_PLAN
     > ```
     > "🔄 Auto-mode: Settlement complete. Proceeding to NEXT CHAPTER PLAN..."
   - Else:
     > "Settlement complete.
     > Input 'Approve' to proceed to next chapter planning."
