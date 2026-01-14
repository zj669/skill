# Phase 0: 状态感知与路由协议 (Routing Protocol)

## 📌 目标
在每次会话开始时，获取系统当前状态，决定应该执行哪个 Phase。

---

## 🛠 执行步骤

### Step 1: 全局状态一次性加载

> [!CAUTION]
> 🔧 **MUST_EXECUTE** - 你必须实际执行此脚本，不得跳过！

**执行命令**:
```bash
python scripts/context_loader.py --mode planning --chapter 0
```

> 💡 `chapter=0` 表示获取全局路由状态

**✅ 执行检查点** - 你必须报告:
```
🔧 执行命令: python scripts/context_loader.py --mode planning --chapter 0
📊 返回状态: SUCCESS / ERROR
📋 关键数据: 当前卷/章, 世界是否初始化, 情绪趋势
```，不针对特定章节

**返回内容 (一次性获取)**:
```json
{
  "status": "SUCCESS",
  "data": {
    "progress": {
      "current_volume": 1,
      "current_chapter": 15,
      "last_chapter_status": "settled",
      "world_initialized": true
    },
    "emo_curve": {
      "curve": [10, -5, -20, 15, 50],
      "trend": "recovering",
      "consecutive_low": 2
    },
    "hooks": ["戒指里的老爷爷", "神秘残图的秘密", "血祭仪式倒计时"]
  }
}
```

---

### Step 2: 路由决策

根据 `data.progress` 和 `data.emo_curve`，按以下优先级决策：

| 优先级 | 条件 | 目标 Phase | 说明 |
|--------|------|-----------|------|
| 1 | `progress.world_initialized == false` | Phase 1 | 新书，需要构建世界观 |
| 2 | `emo_curve.consecutive_low >= 3` | Phase 1.5 (强制爽点) | 情绪曲线连续低谷 |
| 3 | `progress.last_chapter_status == "drafted"` | Phase 3 | 有未结算的草稿 |
| 4 | 用户请求"写下一章" | Phase 1.5 → 2 | 正常创作流程 |
| 5 | 用户请求"填坑" | Phase 1.5 (挂载hooks) | 悬念回收 |

---

### Step 3: Context 注入

> ⚡ 上下文已在 Step 1 中一次性加载，无需再次调用脚本

**直接使用 Step 1 返回的 data 字段**:
- `data.hooks` → 未决悬念列表
- `data.emo_curve` → 情绪曲线建议  
- `data.progress` → 当前进度

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
