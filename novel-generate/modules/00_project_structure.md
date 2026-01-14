# 小说项目目录结构规范 (Project Structure)

## 根目录结构

```
novel-project/
├── project_status.json      # 全局状态文件
├── config/
│   └── settings.json        # 项目配置
│
├── world_bible/             # 世界观设定 (Phase 1)
│   ├── levels.md            # 境界体系
│   ├── geography.md         # 地理设定
│   ├── items.md             # 物品系统
│   ├── factions.md          # 势力关系
│   └── techniques.md        # 功法体系
│
├── char_cards/              # 角色卡片
│   ├── protagonist.json     # 主角状态
│   └── npcs/                # NPC角色
│       └── {name}.json
│
├── outlines/                # 大纲文件
│   ├── novel_architecture.md    # 全书架构
│   └── volumes/
│       └── volume_{n}.json      # 卷级大纲
│
└── volumes/                 # 正文内容 (按卷组织)
    └── volume_{n}/
        └── chapters/
            └── chapter_{m}/     # 每章独立目录
                ├── outline.md       # 本章细纲
                ├── beat_sheet.json  # 节拍表
                ├── draft.md         # 粗稿
                ├── polished.md      # 润色稿
                ├── final.md         # 定稿
                └── execute_logs/    # 执行日志目录
                    ├── context.json     # 上下文快照
                    ├── preflight.json   # 预检结果
                    ├── continuity.json  # 连贯性检查
                    ├── polish_report.json # 润色报告
                    └── settlement.json  # 结算记录
```

---

## 📁 execute_logs 详细说明

每章的 `execute_logs/` 目录记录完整的执行过程，便于追溯和调试。

### 1. context.json (上下文快照)
```json
{
  "timestamp": "2024-01-14T17:30:00",
  "chapter": 16,
  "context_loader_output": {
    "previous_chapter_tail": "...",
    "active_hooks": [...],
    "protagonist": {...},
    "emo_curve": [...]
  }
}
```

### 2. preflight.json (预检结果)
```json
{
  "timestamp": "2024-01-14T17:31:00",
  "status": "PASS",
  "checks": {
    "inventory": "PASS",
    "character_alive": "PASS",
    "skill_available": "PASS"
  },
  "warnings": []
}
```

### 3. continuity.json (连贯性检查)
```json
{
  "timestamp": "2024-01-14T17:45:00",
  "status": "PASS",
  "issues": [],
  "time_anchor": "夜晚",
  "space_anchor": "山洞",
  "emotion_anchor": "紧张"
}
```

### 4. polish_report.json (润色报告)
```json
{
  "timestamp": "2024-01-14T17:50:00",
  "deai_changes": 12,
  "rhythm_adjustments": 8,
  "sensory_additions": 15,
  "word_count_before": 3420,
  "word_count_after": 3510
}
```

### 5. settlement.json (结算记录)
```json
{
  "timestamp": "2024-01-14T18:00:00",
  "status": "SUCCESS",
  "changes": {
    "inventory_add": ["王家令牌"],
    "inventory_remove": ["灵力恢复丹"],
    "relations_updated": [{"target": "王虎", "change": "DEAD"}],
    "hooks_resolved": ["王家追杀"],
    "hooks_added": ["神秘剑主"]
  }
}
```

---

## 🔧 脚本输出规范

所有脚本必须支持 `--output-dir` 参数，将结果写入指定目录：

```bash
# 上下文加载 - 输出到执行日志
python scripts/context_loader.py --mode writing --chapter 16 \
  --output-dir "volumes/volume_1/chapters/chapter_16/execute_logs"

# 连贯性检查 - 输出到执行日志  
python scripts/continuity_checker.py --current 16 \
  --output-dir "volumes/volume_1/chapters/chapter_16/execute_logs"

# 结算 - 输出到执行日志
python scripts/state_manager.py --action settlement --chapter 16 \
  --output-dir "volumes/volume_1/chapters/chapter_16/execute_logs"
```

---

## 📂 目录创建规则

AI在开始新章节写作时，必须首先确保目录存在：

```bash
# 在Step 0之前执行
mkdir -p volumes/volume_{v}/chapters/chapter_{c}/execute_logs
```

或通过脚本自动创建：
```bash
python scripts/state_manager.py --action init_chapter --volume {v} --chapter {c}
```
