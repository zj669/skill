# Phase 1: 世界观构建协议 (World Building Protocol)

## 📌 目标
构建小说的"数据地基"，包括概念层、数据层和知识层。

---

## 🎭 Sub-Skill: World_Builder

**角色定位**: 你是世界设计师，负责搭建整个小说的底层架构。

**核心产出**:
1. **概念层**: 核心梗 (Hook) 与三幕式架构
2. **数据层**: 主角初始状态 (`protagonist.json`)
3. **知识层**: RAG 知识库 (`world_bible/*.md`)

---

## 🛠 执行步骤

### Step 1: 核心概念锚定 (Concept Anchoring)

**输入**: 用户配置
```json
{
  "topic": "凡人流修仙",
  "genre": "热血爽文",
  "target_words": 1000000,
  "protagonist_type": "隐忍型"
}
```

**生成内容**:
- 一句话核心梗概（雪花写作法第一层）
- 核心冲突定义（如：个人成长 vs 资源垄断）
- 三大颠覆点预设（世界观反转节点）

**输出**: `core_seed` (内存变量，供后续步骤引用)

---

### Step 2: 设定文档生成 (World Bible)

**分块生成以下文档**:

| 文件 | 内容 | 用途 |
|------|------|------|
| `world_bible/levels.md` | 境界体系：练气→筑基→金丹...每级寿元/战力 | 战力锚点参考 |
| `world_bible/geography.md` | 大陆板块、宗门分布、禁地设定 | 场景描写素材 |
| `world_bible/items.md` | 灵石汇率、丹药等级、法宝品阶 | 物品校验依据 |
| `world_bible/factions.md` | 势力关系、初始友好度 | 关系图初始化 |
| `world_bible/techniques.md` | 功法体系、属性相克 | 战斗描写参考 |

**RAG 入库**:
```bash
python scripts/rag_engine.py --action init --source_dir "world_bible/"
```

---

### Step 3: 角色初始化 (Character Init) 🚨 CRITICAL

**必须输出符合 Schema 的 JSON**:
```json
{
  "name": "叶凡",
  "level": "练气一层",
  "age": 16,
  "lifespan": 100,
  "spirit_root": "木灵根",
  "spirit_power": { "current": 100, "max": 100 },
  "inventory": ["破旧铁剑", "干粮x3"],
  "skills": [],
  "golden_finger": "神秘戒指",
  "voice": {
    "tone": "沉稳内敛",
    "samples": ["你觉得我会信？", "有些事，做了就是做了。"]
  }
}
```

**入库校验**:
```bash
python scripts/state_manager.py --action init_character --json "{json_data}"
```

**Red Light Check**:
- JSON 格式错误 → 重新生成
- 初始物品不在 `items.md` 中 → 重新生成
- 境界不在 `levels.md` 中 → 重新生成

---

### Step 4: 剧情架构总览 (Plot Architecture)

**基于三幕式结构生成**:
```markdown
## 开篇卷 (第1-50章)
- **目标**: 主角从凡人到筑基
- **核心冲突**: 生存困境
- **高潮**: 筑基突破

## 中盘卷 (第51-150章)
- **目标**: 主角在宗门崛起
- **核心冲突**: 门派斗争
- **高潮**: 晋升核心弟子

## 大结局 (第151-300章)
- **目标**: 主角问鼎修仙界
- **核心冲突**: 终极反派
- **高潮**: 飞升/破碎虚空
```

**输出**: `outlines/novel_architecture.md`

---

## 📄 交付产物清单

| 文件/数据 | 类型 | 用途 |
|-----------|------|------|
| `world_bible/*.md` | 知识 | RAG 素材库 |
| `char_cards/protagonist.json` | 数据 | 主角初始存档 |
| `outlines/novel_architecture.md` | 文本 | 全书架构总览 |
| `.vector_store/` | 索引 | 向量检索索引 |

---

## 🛑 Stop Point
> "世界观构建完成。
> 
> **请审核以下内容**:
> 1. `world_bible/levels.md` - 境界体系是否合理
> 2. `char_cards/protagonist.json` - 主角初始属性是否正确
> 3. `outlines/novel_architecture.md` - 剧情架构是否符合预期
> 
> 输入 'Approve' 进入剧情编排阶段，或提出修改意见。"