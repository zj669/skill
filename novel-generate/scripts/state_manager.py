"""
Novel-Generate 状态管理器
负责 MySQL/Redis/JSON 的读写操作，提供 CLI 接口

功能：
- 章节进度管理
- 情绪曲线 (Redis)
- 悬念管理 (Redis)
- 人物状态 (JSON + MySQL 快照)
- 事件日志 (MySQL)
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Any
import logging

from env_config import get_settings
from db_connector import get_mysql, get_redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


# ============================================================
# JSON 文件操作
# ============================================================

def load_character(name: str = "protagonist", novel_id: str = None) -> dict:
    """加载角色 JSON 文件"""
    novel_id = novel_id or settings.app.default_novel_id
    file_path = settings.app.char_cards_dir / novel_id / f"{name}.json"
    
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_character(name: str, data: dict, novel_id: str = None) -> None:
    """保存角色 JSON 文件"""
    novel_id = novel_id or settings.app.default_novel_id
    char_dir = settings.app.char_cards_dir / novel_id
    char_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = char_dir / f"{name}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============================================================
# Project Status JSON 操作 (Skill 状态源)
# ============================================================

def sync_project_status(novel_id: str = None) -> dict:
    """同步状态到 project_status.json"""
    novel_id = novel_id or settings.app.default_novel_id
    
    # 获取各方状态
    progress = get_progress(novel_id).get("data", {})
    hooks = get_hooks(novel_id).get("data", {}).get("hooks", [])
    
    # 决定当前的 process_step
    # 这是一个简化逻辑，实际可能需要更复杂的判断，或者由外部传入
    # 这里我们主要负责同步数据，process_step 的流转由 skill 显式调用 update_step 更新
    
    # 尝试读取现有的 project_status.json 以保留 process_step 和 config
    current_status = {}
    status_file = Path("project_status.json")
    if status_file.exists():
        try:
            with open(status_file, "r", encoding="utf-8") as f:
                current_status = json.load(f)
        except:
            pass
            
    # 构建新状态
    new_status = {
        "novel_id": novel_id,
        "updated_at": datetime.now().isoformat(),
        "config": {
            "auto_mode": current_status.get("config", {}).get("auto_mode", False)
        },
        "cursor": {
            "volume": progress.get("current_volume", 1),
            "chapter": progress.get("current_chapter", 0),
            "process_step": current_status.get("cursor", {}).get("process_step", "NEED_WORLD")
        },
        "context": {
            "world_initialized": progress.get("world_initialized", False),
            "last_chapter_status": progress.get("last_chapter_status", "none"),
            "active_hooks_count": len(hooks)
        }
    }
    
    # 写入文件
    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(new_status, f, ensure_ascii=False, indent=2)
        
    return {"status": "SUCCESS", "message": "project_status.json synced", "data": new_status}


def toggle_auto(enable: str = None, novel_id: str = None) -> dict:
    """切换全自动模式 (enable: 'on'/'off' or None to toggle)"""
    novel_id = novel_id or settings.app.default_novel_id
    status_file = Path("project_status.json")
    
    if not status_file.exists():
        sync_project_status(novel_id)
        
    with open(status_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    current_mode = data.get("config", {}).get("auto_mode", False)
    
    if enable:
        new_mode = (enable.lower() == "true" or enable.lower() == "on")
    else:
        new_mode = not current_mode
        
    if "config" not in data:
        data["config"] = {}
    data["config"]["auto_mode"] = new_mode
    data["updated_at"] = datetime.now().isoformat()
    
    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    return {"status": "SUCCESS", "message": f"Auto-mode set to {new_mode}", "auto_mode": new_mode}


def update_step(step: str, novel_id: str = None) -> dict:
    """显式更新 process_step"""
    novel_id = novel_id or settings.app.default_novel_id
    
    status_file = Path("project_status.json")
    if not status_file.exists():
        sync_project_status(novel_id)
        
    with open(status_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    data["cursor"]["process_step"] = step
    data["updated_at"] = datetime.now().isoformat()
    
    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    return {"status": "SUCCESS", "message": f"Step updated to {step}"}


def init_project(novel_id: str = None) -> dict:
    """初始化项目状态"""
    novel_id = novel_id or settings.app.default_novel_id
    
    # 确保数据库有基础记录
    get_progress(novel_id)
    
    # 创建 project_status.json
    result = sync_project_status(novel_id)
    
    # 设置初始步骤
    update_step("NEED_WORLD", novel_id)
    
    return result


# ============================================================
# MySQL 操作 - 进度管理
# ============================================================

def get_progress(novel_id: str = None) -> dict:
    """获取当前章节进度"""
    novel_id = novel_id or settings.app.default_novel_id
    mysql = get_mysql()
    
    row = mysql.fetch_one(
        "SELECT * FROM novel_progress WHERE novel_id = %s",
        (novel_id,)
    )
    
    if row:
        return {
            "status": "SUCCESS",
            "data": {
                "current_volume": row["current_volume"],
                "current_chapter": row["current_chapter"],
                "last_chapter_status": row["last_chapter_status"],
                "world_initialized": bool(row["world_initialized"])
            }
        }
    
    return {
        "status": "SUCCESS",
        "data": {
            "current_volume": 1,
            "current_chapter": 0,
            "last_chapter_status": "none",
            "world_initialized": False
        }
    }


def update_progress(novel_id: str, chapter: int = None, status: str = None, 
                    world_initialized: bool = None) -> dict:
    """更新章节进度"""
    novel_id = novel_id or settings.app.default_novel_id
    mysql = get_mysql()
    
    # 构建更新字段
    updates = []
    params = []
    
    if chapter is not None:
        updates.append("current_chapter = %s")
        params.append(chapter)
    if status is not None:
        updates.append("last_chapter_status = %s")
        params.append(status)
    if world_initialized is not None:
        updates.append("world_initialized = %s")
        params.append(world_initialized)
    
    if not updates:
        return {"status": "SUCCESS", "message": "No updates specified"}
    
    params.append(novel_id)
    
    mysql.execute(
        f"UPDATE novel_progress SET {', '.join(updates)} WHERE novel_id = %s",
        tuple(params)
    )
    
    # 自动同步到 JSON
    sync_project_status(novel_id)
    
    return {"status": "SUCCESS", "message": "Progress updated"}


# ============================================================
# MySQL 操作 - 事件日志
# ============================================================

def log_event(novel_id: str, chapter: int, event_type: str, 
              target: str, content: str, meta_data: dict = None) -> dict:
    """记录事件到日志"""
    mysql = get_mysql()
    
    mysql.execute(
        """INSERT INTO event_timeline 
           (novel_id, chapter_num, event_type, target, content, meta_data)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (novel_id, chapter, event_type, target, content, 
         json.dumps(meta_data) if meta_data else None)
    )
    
    return {"status": "SUCCESS", "message": f"Event logged: {event_type} - {target}"}


def check_event(novel_id: str, event_type: str, target: str) -> dict:
    """检查事件是否发生过 (用于防止死人复活等)"""
    mysql = get_mysql()
    
    row = mysql.fetch_one(
        """SELECT * FROM event_timeline 
           WHERE novel_id = %s AND event_type = %s AND target = %s
           ORDER BY created_at DESC LIMIT 1""",
        (novel_id, event_type, target)
    )
    
    return {
        "status": "SUCCESS",
        "data": {
            "exists": row is not None,
            "event": row
        }
    }


# ============================================================
# MySQL 操作 - 状态快照
# ============================================================

def save_snapshot(novel_id: str, chapter: int, character_name: str, 
                  state_json: dict) -> dict:
    """保存角色状态快照"""
    mysql = get_mysql()
    
    mysql.execute(
        """INSERT INTO character_snapshot 
           (novel_id, chapter_num, character_name, state_json)
           VALUES (%s, %s, %s, %s)
           ON DUPLICATE KEY UPDATE state_json = VALUES(state_json)""",
        (novel_id, chapter, character_name, json.dumps(state_json))
    )
    
    return {"status": "SUCCESS", "message": f"Snapshot saved for chapter {chapter}"}


def load_snapshot(novel_id: str, chapter: int, character_name: str) -> dict:
    """加载指定章节的角色状态快照"""
    mysql = get_mysql()
    
    row = mysql.fetch_one(
        """SELECT state_json FROM character_snapshot
           WHERE novel_id = %s AND chapter_num = %s AND character_name = %s""",
        (novel_id, chapter, character_name)
    )
    
    if row:
        return {
            "status": "SUCCESS",
            "data": json.loads(row["state_json"]) if isinstance(row["state_json"], str) 
                    else row["state_json"]
        }
    
    return {"status": "FAILED", "error_code": "E101", "message": "Snapshot not found"}


# ============================================================
# Redis 操作 - 情绪曲线
# ============================================================

def get_emo_curve(novel_id: str = None, count: int = 5) -> dict:
    """获取情绪曲线"""
    novel_id = novel_id or settings.app.default_novel_id
    redis_client = get_redis().client
    key = f"novel:{novel_id}:emo_curve"
    
    curve = redis_client.lrange(key, 0, count - 1)
    curve = [int(x) for x in curve] if curve else []
    
    # 计算趋势
    consecutive_low = 0
    low_threshold = 20
    for score in curve:
        if score < low_threshold:
            consecutive_low += 1
        else:
            break
    
    trend = "neutral"
    if len(curve) >= 2:
        if curve[0] > curve[-1]:
            trend = "rising"
        elif curve[0] < curve[-1]:
            trend = "falling"
    
    return {
        "status": "SUCCESS",
        "data": {
            "curve": curve,
            "trend": trend,
            "consecutive_low": consecutive_low
        }
    }


def update_emo(novel_id: str = None, score: int = 50) -> dict:
    """更新情绪分数"""
    novel_id = novel_id or settings.app.default_novel_id
    redis_client = get_redis().client
    key = f"novel:{novel_id}:emo_curve"
    
    redis_client.lpush(key, score)
    redis_client.ltrim(key, 0, 19)  # 保留最近20章
    
    return {"status": "SUCCESS", "message": f"Emo score {score} recorded"}


# ============================================================
# Redis 操作 - 悬念管理
# ============================================================

def get_hooks(novel_id: str = None) -> dict:
    """获取未决悬念列表"""
    novel_id = novel_id or settings.app.default_novel_id
    redis_client = get_redis().client
    key = f"novel:{novel_id}:hooks"
    
    hooks = list(redis_client.smembers(key))
    
    return {
        "status": "SUCCESS",
        "data": {
            "hooks": hooks,
            "count": len(hooks)
        }
    }


def update_hooks(novel_id: str = None, resolved: list = None, 
                 added: list = None) -> dict:
    """更新悬念列表"""
    novel_id = novel_id or settings.app.default_novel_id
    redis_client = get_redis().client
    key = f"novel:{novel_id}:hooks"
    
    if resolved:
        for hook in resolved:
            redis_client.srem(key, hook)
    
    if added:
        for hook in added:
            redis_client.sadd(key, hook)
    
    return {"status": "SUCCESS", "message": "Hooks updated"}


# ============================================================
# 角色状态操作
# ============================================================

def init_character(json_data: str, novel_id: str = None) -> dict:
    """初始化角色"""
    novel_id = novel_id or settings.app.default_novel_id
    
    try:
        data = json.loads(json_data)
        name = data.get("name", "protagonist")
        save_character(name, data, novel_id)
        
        # 同时初始化进度
        mysql = get_mysql()
        mysql.execute(
            """INSERT INTO novel_progress (novel_id, world_initialized)
               VALUES (%s, TRUE)
               ON DUPLICATE KEY UPDATE world_initialized = TRUE""",
            (novel_id,)
        )
        
        return {"status": "SUCCESS", "message": f"Character {name} initialized"}
    except json.JSONDecodeError as e:
        return {"status": "FAILED", "error_code": "E100", "message": f"JSON格式错误: {e}"}


def update_inventory(novel_id: str = None, remove: list = None, 
                     add: list = None) -> dict:
    """更新背包"""
    novel_id = novel_id or settings.app.default_novel_id
    char = load_character("protagonist", novel_id)
    
    if not char:
        return {"status": "FAILED", "error_code": "E101", "message": "角色不存在"}
    
    inventory = char.get("inventory", [])
    
    if remove:
        for item in remove:
            if item in inventory:
                inventory.remove(item)
    
    if add:
        inventory.extend(add)
    
    char["inventory"] = inventory
    save_character("protagonist", char, novel_id)
    
    return {"status": "SUCCESS", "data": {"inventory": inventory}}


# ============================================================
# Pre-Flight 校验
# ============================================================

def preflight(scene_plan: str, novel_id: str = None) -> dict:
    """前置校验"""
    novel_id = novel_id or settings.app.default_novel_id
    
    try:
        plan = json.loads(scene_plan)
        char = load_character("protagonist", novel_id)
        mysql = get_mysql()
        
        errors = []
        warnings = []
        
        # 1. 检查物品可用性
        items_used = plan.get("items_used", [])
        inventory = char.get("inventory", [])
        for item in items_used:
            if item not in inventory:
                errors.append({
                    "code": "E001",
                    "message": f"物品不存在: {item}"
                })
        
        # 2. 检查角色是否死亡
        characters = plan.get("characters", [])
        for char_name in characters:
            death_event = check_event(novel_id, "death", char_name)
            if death_event["data"]["exists"]:
                errors.append({
                    "code": "E002",
                    "message": f"角色已死亡: {char_name}"
                })
        
        # 3. 检查技能是否已学习
        skills_used = plan.get("skills_used", [])
        char_skills = char.get("skills", [])
        for skill in skills_used:
            skill_name = skill if isinstance(skill, str) else skill.get("name")
            if skill_name not in [s.get("name") if isinstance(s, dict) else s for s in char_skills]:
                errors.append({
                    "code": "E004",
                    "message": f"技能未学习: {skill_name}"
                })
        
        if errors:
            return {
                "status": "FAILED",
                "errors": errors,
                "warnings": warnings
            }
        
        return {"status": "PASS", "warnings": warnings}
    
    except json.JSONDecodeError:
        return {"status": "FAILED", "error_code": "E100", "message": "JSON格式错误"}


def get_voice(characters: str, novel_id: str = None) -> dict:
    """获取角色语气样本"""
    novel_id = novel_id or settings.app.default_novel_id
    
    try:
        char_list = json.loads(characters)
        result = {}
        
        for char_name in char_list:
            char_data = load_character(char_name, novel_id)
            if char_data and "voice" in char_data:
                result[char_name] = char_data["voice"]
        
        return {"status": "SUCCESS", "data": result}
    except json.JSONDecodeError:
        return {"status": "FAILED", "error_code": "E100", "message": "JSON格式错误"}


# ============================================================
# 管理员操作 (Retcon)
# ============================================================

def admin_add(target: str, item: str, note: str, novel_id: str = None) -> dict:
    """管理员添加物品 (Retcon)"""
    novel_id = novel_id or settings.app.default_novel_id
    char = load_character(target, novel_id)
    
    if not char:
        return {"status": "FAILED", "error_code": "E101", "message": "角色不存在"}
    
    inventory = char.get("inventory", [])
    inventory.append(item)
    char["inventory"] = inventory
    
    save_character(target, char, novel_id)
    
    # 记录日志
    log_file = settings.app.logs_dir / "retcon.log"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] [RETCON] Added '{item}' to {target}. Note: {note}\n")
    
    return {"status": "SUCCESS", "message": f"Added {item} to {target}"}


# ============================================================
# 章节摘要操作
# ============================================================

def save_summary(novel_id: str, chapter: int, summary: str) -> dict:
    """保存章节摘要到 MySQL"""
    novel_id = novel_id or settings.app.default_novel_id
    mysql = get_mysql()
    
    mysql.execute(
        """INSERT INTO chapter_summary 
           (novel_id, chapter_num, summary)
           VALUES (%s, %s, %s)
           ON DUPLICATE KEY UPDATE summary = VALUES(summary)""",
        (novel_id, chapter, summary)
    )
    
    return {"status": "SUCCESS", "message": f"Summary saved for chapter {chapter}"}


def get_chapter_summary(novel_id: str, chapter: int) -> dict:
    """获取章节摘要"""
    novel_id = novel_id or settings.app.default_novel_id
    mysql = get_mysql()
    
    row = mysql.fetch_one(
        "SELECT summary FROM chapter_summary WHERE novel_id = %s AND chapter_num = %s",
        (novel_id, chapter)
    )
    
    if row:
        return {"status": "SUCCESS", "data": row["summary"]}
    return {"status": "NOT_FOUND", "data": ""}


def verify_settlement(novel_id: str, chapter: int) -> dict:
    """验证数据结算完整性"""
    novel_id = novel_id or settings.app.default_novel_id
    mysql = get_mysql()
    redis_client = get_redis().client
    
    checks = {}
    all_passed = True
    
    # 1. 检查进度是否更新
    progress = get_progress(novel_id)
    if progress["data"]["current_chapter"] >= chapter:
        checks["progress"] = "OK"
    else:
        checks["progress"] = f"WARN: current_chapter={progress['data']['current_chapter']}, expected >= {chapter}"
    
    # 2. 检查摘要是否存在
    summary_row = mysql.fetch_one(
        "SELECT summary FROM chapter_summary WHERE novel_id = %s AND chapter_num = %s",
        (novel_id, chapter)
    )
    if summary_row:
        checks["summary"] = "OK"
    else:
        checks["summary"] = "MISSING"
        all_passed = False
    
    # 3. 检查快照是否存在
    snapshot_row = mysql.fetch_one(
        "SELECT id FROM character_snapshot WHERE novel_id = %s AND chapter_num = %s",
        (novel_id, chapter)
    )
    if snapshot_row:
        checks["snapshot"] = "OK"
    else:
        checks["snapshot"] = "MISSING"
        all_passed = False
    
    # 4. 检查情绪曲线是否有记录
    emo_key = f"novel:{novel_id}:emo_curve"
    emo_len = redis_client.llen(emo_key)
    if emo_len >= chapter:
        checks["emo_curve"] = "OK"
    else:
        checks["emo_curve"] = f"WARN: {emo_len} records, expected >= {chapter}"
    
    return {
        "status": "SUCCESS" if all_passed else "INCOMPLETE",
        "data": {
            "chapter": chapter,
            "checks": checks,
            "all_passed": all_passed
        }
    }


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Novel-Generate State Manager")
    parser.add_argument("--action", required=True, help="Action to perform")
    parser.add_argument("--novel_id", help="Novel ID")
    parser.add_argument("--json", help="JSON data")
    parser.add_argument("--remove", help="Items to remove (JSON array)")
    parser.add_argument("--add", help="Items to add (JSON array)")
    parser.add_argument("--scene_plan", help="Scene plan JSON")
    parser.add_argument("--characters", help="Character names (JSON array)")
    parser.add_argument("--chapter", type=int, help="Chapter number")
    parser.add_argument("--summary", help="Chapter summary")
    parser.add_argument("--score", type=int, help="Emo score")
    parser.add_argument("--resolved", help="Resolved hooks (JSON array)")
    parser.add_argument("--added", help="Added hooks (JSON array)")
    parser.add_argument("--target", help="Target character")
    parser.add_argument("--item", help="Item name")
    parser.add_argument("--note", help="Admin note")
    parser.add_argument("--count", type=int, default=5, help="Count")
    parser.add_argument("--event_type", help="Event type")
    parser.add_argument("--content", help="Event content")
    parser.add_argument("--meta_data", help="Event meta data (JSON)")
    parser.add_argument("--status", help="Chapter status")
    parser.add_argument("--character_name", default="protagonist", help="Character name")
    parser.add_argument("--enable", help="Enable auto mode (on/off)")
    
    args = parser.parse_args()
    novel_id = args.novel_id or settings.app.default_novel_id
    
    action_map = {
        "get_progress": lambda: get_progress(novel_id),
        "update_progress": lambda: update_progress(
            novel_id, args.chapter, args.status
        ),
        "get_emo_curve": lambda: get_emo_curve(novel_id, args.count),
        "update_emo": lambda: update_emo(novel_id, args.score),
        "get_hooks": lambda: get_hooks(novel_id),
        "update_hooks": lambda: update_hooks(
            novel_id,
            json.loads(args.resolved) if args.resolved else None,
            json.loads(args.added) if args.added else None
        ),
        "init_character": lambda: init_character(args.json, novel_id),
        "update_inventory": lambda: update_inventory(
            novel_id,
            json.loads(args.remove) if args.remove else None,
            json.loads(args.add) if args.add else None
        ),
        "preflight": lambda: preflight(args.scene_plan, novel_id),
        "get_voice": lambda: get_voice(args.characters, novel_id),
        "admin_add": lambda: admin_add(args.target, args.item, args.note, novel_id),
        "log_event": lambda: log_event(
            novel_id, args.chapter, args.event_type, args.target, args.content,
            json.loads(args.meta_data) if args.meta_data else None
        ),
        "check_event": lambda: check_event(novel_id, args.event_type, args.target),
        "save_snapshot": lambda: save_snapshot(
            novel_id, args.chapter, args.character_name,
            load_character(args.character_name, novel_id)
        ),
        "load_snapshot": lambda: load_snapshot(
            novel_id, args.chapter, args.character_name
        ),
        "save_summary": lambda: save_summary(novel_id, args.chapter, args.summary),
        "verify_settlement": lambda: verify_settlement(novel_id, args.chapter),
        # 新增项目状态管理
        "sync_project_status": lambda: sync_project_status(novel_id),
        "update_step": lambda: update_step(args.status, novel_id),
        "init_project": lambda: init_project(novel_id),
        "toggle_auto": lambda: toggle_auto(args.enable, novel_id),
        "next_chapter": lambda: next_chapter(novel_id),
    }
    
    if args.action in action_map:
        result = action_map[args.action]()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result.get("status") in ["SUCCESS", "PASS"] else 1)
    else:
        print(json.dumps({"status": "FAILED", "message": f"Unknown action: {args.action}"}))
        sys.exit(1)



def next_chapter(novel_id: str = None) -> dict:
    """进入下一章 (章节号+1)"""
    novel_id = novel_id or settings.app.default_novel_id
    status_file = Path("project_status.json")
    
    # 1. 更新数据库 ensure persistence
    if not status_file.exists():
        sync_project_status(novel_id)
        
    with open(status_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    current_chap = data.get("cursor", {}).get("chapter", 0)
    new_chap = current_chap + 1
    
    data["cursor"]["chapter"] = new_chap
    data["updated_at"] = datetime.now().isoformat()
    
    # Update DB progress too
    try:
        mysql = get_mysql()
        mysql.execute(
            "UPDATE novel_progress SET current_chapter = %s WHERE novel_id = %s",
            (new_chap, novel_id)
        )
    except:
        pass
    
    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    return {"status": "SUCCESS", "message": f"Moved to chapter {new_chap}", "chapter": new_chap}


if __name__ == "__main__":
    main()
