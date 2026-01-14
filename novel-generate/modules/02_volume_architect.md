# Phase 2: 卷级大纲架构 (Volume Architect)

## 📌 目标
将全书大纲拆解为可执行的卷级大纲，细化每一章的核心看点。

---

## 🎭 Sub-Skill: Volume_Architect

**角色定位**: 你是分卷主编，负责规划当前卷的具体内容。

**核心产出**:
- `volumes/volume_{n}/outline.json` (当前卷详纲)

---

## 🛠 执行步骤

### Step 1: 卷目标确认 (Volume Scoping)

**读取 Context**:
```bash
python scripts/context_loader.py --mode planning --chapter 0
```
- 获取当前卷号 (`current_volume`)
- 读取全书大纲中对应卷的规划

### Step 2: 章节列表生成 (Chapter List Generation)

**任务**:
为本卷生成 40-60 个章节的标题和一句话梗概。

**要求**:
- **节奏把控**: 每 3-5 章一个小高潮，10-15 章一个大高潮。
- **爽点分布**: 确保每章都有期待感或爽点。
- **钩子埋设**: 关键节点埋下伏笔。

### Step 3: 数据落地 (Save Outline)

> [!CAUTION]
> 🔧 **MUST_EXECUTE** - 你必须保存卷纲数据！

**操作**:
1. 创建目录 `volumes/volume_{n}/`
2. 保存 `outline.json`

```bash
# 示例：由于目前没有专门的大纲生成脚本，建议直接用 write_file 工具写入文件
# 或者扩展 state_manager 来支持大纲存取
```

**JSON 结构模板**:
```json
{
  "volume_id": 1,
  "title": "云州风云",
  "theme": "生存与崛起",
  "chapters": [
    {
      "num": 1,
      "title": "落魄少年",
      "summary": "主角被家族排挤，独自上山采药，意外获得神秘戒指。",
      "main_character": "叶凡",
      "items": ["神秘戒指"]
    },
    {
      "num": 2,
      "title": "药老苏醒",
      "summary": "戒指中钻出灵魂体药老，传授《焚诀》。",
      "key_point": "金手指上线"
    }
  ]
}
```

---

## 🛑 Stop Point / 🔄 Auto-Pilot

**Logic**:
1. **Check Auto-Mode**:
   - If `context.auto_mode` is **True**:
     > 🔧 **MUST_EXECUTE**
     > ```bash
     > python scripts/state_manager.py --action update_step --status NEED_PLAN
     > ```
     > "🔄 Auto-mode: Volume outline created. Proceeding to CHAPTER PLAN..."
   - Else:
     > "Volume outline created. Please review `volumes/volume_{n}/outline.json`.
     > Input 'Approve' to begin chapter planning."
