# Novel-Generate Redis 数据结构说明

## Key 命名规范

所有 Key 遵循 `novel:{novel_id}:{data_type}` 格式。

---

## 1. 情绪曲线 (Emotional Curve)

**Key**: `novel:{novel_id}:emo_curve`
**Type**: List (FIFO 队列)
**说明**: 存储最近 N 章的情绪分数，用于判断是否需要强制"爆发"剧情

### 操作示例

```redis
# 新章节完成后，添加情绪分数 (从左侧推入)
LPUSH novel:001:emo_curve 45

# 保留最近 20 章的数据
LTRIM novel:001:emo_curve 0 19

# 获取最近 5 章的情绪分数
LRANGE novel:001:emo_curve 0 4
# 返回: ["45", "30", "-10", "60", "25"]

# 计算连续低谷次数 (由脚本处理)
# 规则: score < 20 视为低谷
```

---

## 2. 未决悬念 (Unresolved Hooks)

**Key**: `novel:{novel_id}:hooks`
**Type**: Set
**说明**: 存储所有"挖了但还没填的坑"

### 操作示例

```redis
# 添加新悬念 (Phase 3 数据结算时)
SADD novel:001:hooks "戒指里的老爷爷" "神秘残图的秘密"

# 回收悬念 (当悬念被解决时)
SREM novel:001:hooks "戒指里的老爷爷"

# 获取所有悬念
SMEMBERS novel:001:hooks
# 返回: ["神秘残图的秘密", "血祭仪式倒计时"]

# 随机获取一个悬念 (用于强制回收)
SRANDMEMBER novel:001:hooks

# 获取悬念数量
SCARD novel:001:hooks
```

---

## 3. 暗线进度 (Background Threads)

**Key**: `novel:{novel_id}:threads`
**Type**: Hash
**说明**: 存储后台倒计时事件的进度

### 操作示例

```redis
# 设置暗线进度
HSET novel:001:threads blood_ritual_progress 30
HSET novel:001:threads hidden_enemy_awakening 0

# 每章结束后增加进度
HINCRBY novel:001:threads blood_ritual_progress 10

# 获取所有暗线
HGETALL novel:001:threads
# 返回: {"blood_ritual_progress": "40", "hidden_enemy_awakening": "5"}

# 获取单个暗线进度
HGET novel:001:threads blood_ritual_progress

# 当进度达到 100 时，触发事件并删除
HDEL novel:001:threads blood_ritual_progress
```

---

## 4. 写作锁 (Write Lock)

**Key**: `novel:{novel_id}:write_lock`
**Type**: String (with TTL)
**说明**: 防止并发写作冲突

### 操作示例

```redis
# 获取写作锁 (设置 10 分钟过期)
SET novel:001:write_lock "session_abc" NX EX 600

# 检查锁是否存在
EXISTS novel:001:write_lock

# 释放锁
DEL novel:001:write_lock
```

---

## 5. 最近章节缓存 (Recent Chapters Cache)

**Key**: `novel:{novel_id}:recent_chapters`
**Type**: List
**说明**: 缓存最近几章的摘要，避免频繁查库

### 操作示例

```redis
# 添加最新章节摘要 (JSON 格式)
LPUSH novel:001:recent_chapters '{"chapter":16,"title":"血战矿洞","summary":"..."}'

# 保留最近 5 章
LTRIM novel:001:recent_chapters 0 4

# 获取最近 3 章
LRANGE novel:001:recent_chapters 0 2
```

---

## 初始化脚本 (可选)

当创建新小说时，可以运行以下命令初始化数据结构：

```redis
# 初始化空的情绪曲线
DEL novel:{novel_id}:emo_curve

# 初始化空的悬念集合
DEL novel:{novel_id}:hooks

# 初始化暗线进度
DEL novel:{novel_id}:threads

# 设置小说元信息
HSET novel:{novel_id}:meta name "小说名称" created_at "2026-01-14"
```
