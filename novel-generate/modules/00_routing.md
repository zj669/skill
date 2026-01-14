# Phase 0: 状态感知与路由协议 (Routing Protocol)

## 📌 目标
在每次会话开始时，获取系统当前状态，决定应该执行哪个 Phase。

---

## 🛠 执行步骤

### Step 1: 数据库状态查询

**MySQL 查询** (章节进度):
```bash
python scripts/state_manager.py --action get_progress
```

**预期返回**:
```json
{
  "current_volume": 1,
  "current_chapter": 15,
  "last_chapter_status": "settled",
  "world_initialized": true
}
```

---

### Step 2: Redis 状态查询

**情绪曲线**:
```bash
python scripts/state_manager.py --action get_emo_curve --count 5
```

**预期返回**:
```json
{
  "curve": [10, -5, -20, 15, 50],
  "trend": "recovering",
  "consecutive_low": 2
}
```

**未决悬念**:
```bash
python scripts/state_manager.py --action get_hooks
```

**预期返回**:
```json
{
  "hooks": ["戒指里的老爷爷", "神秘残图的秘密", "血祭仪式倒计时"]
}
```

---

### Step 3: 路由决策

根据查询结果，按以下优先级决策：

| 优先级 | 条件 | 目标 Phase | 说明 |
|--------|------|-----------|------|
| 1 | `world_initialized == false` | Phase 1 | 新书，需要构建世界观 |
| 2 | `consecutive_low >= 3` | Phase 1.5 (强制爽点) | 情绪曲线连续低谷 |
| 3 | `last_chapter_status == "drafted"` | Phase 3 | 有未结算的草稿 |
| 4 | 用户请求"写下一章" | Phase 1.5 → 2 | 正常创作流程 |
| 5 | 用户请求"填坑" | Phase 1.5 (挂载hooks) | 悬念回收 |

---

### Step 4: Context 注入

根据目标 Phase，准备相应的上下文：

**For Phase 1.5 (剧情编排)**:
- 上一章摘要 (MySQL)
- 未决悬念列表 (Redis)
- 情绪曲线建议 (Redis)

**For Phase 2 (正文写作)**:
- 本章细纲
- 当前场景涉及角色的 JSON 状态
- RAG 检索的环境描写素材

---

## 📄 交付物

| 输出 | 类型 | 用途 |
|------|------|------|
| `routing_decision` | 变量 | 决定跳转到哪个 Phase |
| `context_payload` | JSON | 传递给目标 Phase 的上下文 |

## 🛑 Stop Point
> "状态感知完成。当前进度：第 {volume} 卷 第 {chapter} 章。
> 推荐动作：{recommended_action}。
> 输入 'Proceed' 继续，或指定其他动作。"
