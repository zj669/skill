-- ============================================================
-- Novel-Generate MySQL 初始化脚本
-- 包含：进度表、摘要表、事件日志表、状态快照表
-- ============================================================

-- 使用数据库
USE novel_db;

-- ============================================================
-- 写作进度表
-- ============================================================
CREATE TABLE IF NOT EXISTS novel_progress (
    id INT PRIMARY KEY AUTO_INCREMENT,
    novel_id VARCHAR(64) NOT NULL COMMENT '小说唯一标识',
    novel_name VARCHAR(255) COMMENT '小说名称',
    current_volume INT DEFAULT 1 COMMENT '当前卷',
    current_chapter INT DEFAULT 0 COMMENT '当前章节',
    last_chapter_status ENUM('none','drafted','settled') DEFAULT 'none' COMMENT '最后章节状态',
    world_initialized BOOLEAN DEFAULT FALSE COMMENT '世界观是否已初始化',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_novel_id (novel_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 章节摘要表
-- ============================================================
CREATE TABLE IF NOT EXISTS chapter_summary (
    id INT PRIMARY KEY AUTO_INCREMENT,
    novel_id VARCHAR(64) NOT NULL COMMENT '小说唯一标识',
    chapter_num INT NOT NULL COMMENT '章节编号',
    title VARCHAR(255) COMMENT '章节标题',
    summary TEXT COMMENT '章节摘要 (用于上下文回顾)',
    emo_score INT COMMENT '情绪评分 (0-100)',
    word_count INT COMMENT '字数统计',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_novel_chapter (novel_id, chapter_num),
    INDEX idx_novel_id (novel_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 事件日志表 (防止死人复活/重复获宝)
-- ============================================================
CREATE TABLE IF NOT EXISTS event_timeline (
    id INT PRIMARY KEY AUTO_INCREMENT,
    novel_id VARCHAR(64) NOT NULL COMMENT '小说唯一标识',
    chapter_num INT NOT NULL COMMENT '发生章节',
    event_type ENUM(
        'death',           -- 角色死亡
        'item_gain',       -- 获得物品
        'item_use',        -- 使用物品
        'item_consume',    -- 消耗物品
        'level_up',        -- 境界突破
        'skill_learn',     -- 学习技能
        'relation_change', -- 关系变化
        'hook_add',        -- 新增悬念
        'hook_resolve'     -- 回收悬念
    ) NOT NULL COMMENT '事件类型',
    target VARCHAR(128) COMMENT '事件目标 (角色名/物品名)',
    content TEXT COMMENT '事件描述 (人类可读)',
    
    -- 优化：结构化元数据，方便脚本查询
    meta_data JSON COMMENT '结构化参数，如 {"item_id":"sword_001","qty":1}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_novel_type (novel_id, event_type),
    INDEX idx_novel_chapter (novel_id, chapter_num),
    INDEX idx_target (target)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 人物状态快照表 (用于逻辑回滚和历史状态查询)
-- ============================================================
CREATE TABLE IF NOT EXISTS character_snapshot (
    id INT PRIMARY KEY AUTO_INCREMENT,
    novel_id VARCHAR(64) NOT NULL COMMENT '小说唯一标识',
    chapter_num INT NOT NULL COMMENT '快照对应的章节',
    character_name VARCHAR(64) NOT NULL COMMENT '角色名称',
    
    -- 核心：直接把整个JSON文件存进去
    state_json JSON NOT NULL COMMENT '包含属性、背包、技能树的完整JSON',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_novel_chap_char (novel_id, chapter_num, character_name),
    INDEX idx_chap_char (chapter_num, character_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 初始化示例数据 (可选)
-- ============================================================

-- 插入一个示例小说进度
INSERT INTO novel_progress (novel_id, novel_name, world_initialized) 
VALUES ('novel_001', '遮天同人', FALSE)
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;
