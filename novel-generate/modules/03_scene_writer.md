# Phase 2: 正文写作协议 (Scene Writer Protocol)

## 📌 目标
基于细纲，生成高质量的章节正文。通过 RAG 检索和状态校验，确保剧情逻辑自洽。

---

## 🎭 Sub-Skill: Scene_Writer

**角色定位**: 你是执行写手，负责将细纲转化为生动的正文。

**核心约束**:
- 严禁凭空创造物品/技能（必须查库）
- 严禁复活已死亡角色（必须查图谱）
- 严禁违反战力锚点（必须查配置）

---

## 🛠 执行步骤

### Step 1: Pre-Flight Check (红灯校验) 🚨

**必须在写作前执行**:
```bash
python scripts/state_manager.py --action preflight --scene_plan "{scene_json}"
```

**校验项目**:
| 检查项 | 数据源 | 失败处理 |
|--------|--------|---------|
| 物品可用性 | JSON (背包) | 跳转 Phase X |
| 角色存活状态 | Neo4j (关系图) | 跳转 Phase X |
| 技能已学习 | JSON (技能树) | 跳转 Phase X |
| 战力合理性 | config.py (锚点) | 跳转 Phase X |

**返回示例**:
```json
{
  "status": "PASS",
  "warnings": ["主角灵力仅剩 30%，无法使用大招"]
}
```

---

### Step 2: 素材挂载 (Context Mounting)

**RAG 检索** (环境/功法描写):
```bash
python scripts/rag_engine.py --query "筑基期战斗场景描写" --top_k 3
```

**角色语气加载** (Few-Shot):
```bash
python scripts/state_manager.py --action get_voice --characters '["叶凡", "老爷爷"]'
```

**返回示例**:
```json
{
  "叶凡": {
    "tone": "沉稳内敛",
    "samples": ["你觉得我会信？", "有些事，做了就是做了。"]
  },
  "老爷爷": {
    "tone": "高深莫测",
    "samples": ["小子，你的造化来了。", "老夫当年..."]
  }
}
```

---

### Step 3: 正文生成

**写作规范**:

1. **场景切换**: 使用 `---` 分隔不同场景
2. **对话格式**: 
   ```
   "台词内容。"角色名说道/道/冷笑道。
   ```
3. **战斗描写**: 必须引用 RAG 检索到的功法特效
4. **字数控制**: 每场景 800-1500 字，全章 3000-5000 字

**禁止事项**:
- ❌ 使用未检索到的功法名称
- ❌ 让角色使用背包里没有的物品
- ❌ 出现"第二天"等时间跳跃（除非细纲明确）

---

### Step 4: 草稿输出

**格式**:
```markdown
# 第 {chapter_num} 章：{chapter_title}

{正文内容}

---
<!-- 元数据 (仅供 Data_Manager 使用) -->
[ITEMS_USED]: ["青锋剑", "灵力恢复丹"]
[ITEMS_GAINED]: ["王家令牌"]
[RELATIONS_CHANGED]: [{"target": "王虎", "change": "DEAD"}]
[EMO_SCORE]: 45
```

---

## 📄 交付物

| 输出 | 类型 | 用途 |
|------|------|------|
| `drafts/chapter_{n}.md` | Markdown | 章节草稿 |
| 正文末尾元数据 | Comment | 供 Data_Manager 解析 |

## 🛑 Stop Point
> "第 {chapter} 章草稿已生成（{word_count} 字）。
> 情绪评分：{emo_score}/100
> 
> 请审核后输入 '定稿' 进行数据结算，或提出修改意见。"
