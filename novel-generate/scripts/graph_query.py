"""
Novel-Generate 图谱查询器
负责 Neo4j 人物关系图谱的查询和更新

功能：
- 关系查询 (仇人/盟友/师徒)
- 关系更新 (击杀/结仇/结盟)
- 角色状态查询
"""

import argparse
import json
import sys
from typing import Optional, List, Dict
import logging

from env_config import get_settings
from db_connector import get_neo4j

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


# ============================================================
# 角色查询
# ============================================================

def get_character(name: str, novel_id: str = None) -> dict:
    """获取角色信息"""
    novel_id = novel_id or settings.app.default_novel_id
    neo4j = get_neo4j()
    
    query = """
    MATCH (c:Character {name: $name, novel_id: $novel_id})
    RETURN c
    """
    
    results = neo4j.run_query(query, {"name": name, "novel_id": novel_id})
    
    if results:
        return {
            "status": "SUCCESS",
            "data": results[0].get("c")
        }
    
    return {"status": "FAILED", "error_code": "E101", "message": f"Character not found: {name}"}


def is_alive(name: str, novel_id: str = None) -> dict:
    """检查角色是否存活"""
    novel_id = novel_id or settings.app.default_novel_id
    neo4j = get_neo4j()
    
    query = """
    MATCH (c:Character {name: $name, novel_id: $novel_id})
    RETURN c.status as status
    """
    
    results = neo4j.run_query(query, {"name": name, "novel_id": novel_id})
    
    if results:
        status = results[0].get("status", "alive")
        return {
            "status": "SUCCESS",
            "data": {
                "name": name,
                "is_alive": status == "alive",
                "character_status": status
            }
        }
    
    # 如果角色不存在，默认视为存活
    return {
        "status": "SUCCESS",
        "data": {
            "name": name,
            "is_alive": True,
            "character_status": "unknown"
        }
    }


# ============================================================
# 关系查询
# ============================================================

def get_enemies(name: str, novel_id: str = None, min_intensity: int = 0) -> dict:
    """获取某角色的仇人列表"""
    novel_id = novel_id or settings.app.default_novel_id
    neo4j = get_neo4j()
    
    query = """
    MATCH (c:Character {name: $name, novel_id: $novel_id})-[r:HATES]->(enemy:Character)
    WHERE r.intensity >= $min_intensity
    RETURN enemy.name as name, r.intensity as intensity, enemy.status as status
    ORDER BY r.intensity DESC
    """
    
    results = neo4j.run_query(query, {
        "name": name, 
        "novel_id": novel_id,
        "min_intensity": min_intensity
    })
    
    return {
        "status": "SUCCESS",
        "data": {
            "character": name,
            "enemies": results
        }
    }


def get_allies(name: str, novel_id: str = None) -> dict:
    """获取某角色的盟友列表"""
    novel_id = novel_id or settings.app.default_novel_id
    neo4j = get_neo4j()
    
    query = """
    MATCH (c:Character {name: $name, novel_id: $novel_id})-[:ALLIED]-(ally:Character)
    RETURN ally.name as name, ally.level as level, ally.status as status
    """
    
    results = neo4j.run_query(query, {"name": name, "novel_id": novel_id})
    
    return {
        "status": "SUCCESS",
        "data": {
            "character": name,
            "allies": results
        }
    }


def get_faction_members(faction_name: str, novel_id: str = None) -> dict:
    """获取势力成员"""
    novel_id = novel_id or settings.app.default_novel_id
    neo4j = get_neo4j()
    
    query = """
    MATCH (c:Character)-[r:BELONGS_TO]->(f:Faction {name: $faction_name, novel_id: $novel_id})
    RETURN c.name as name, c.level as level, r.role as role, c.status as status
    ORDER BY c.level DESC
    """
    
    results = neo4j.run_query(query, {"faction_name": faction_name, "novel_id": novel_id})
    
    return {
        "status": "SUCCESS",
        "data": {
            "faction": faction_name,
            "members": results
        }
    }


def find_path(from_name: str, to_name: str, novel_id: str = None, 
              max_depth: int = 4) -> dict:
    """查找两个角色之间的关系路径"""
    novel_id = novel_id or settings.app.default_novel_id
    neo4j = get_neo4j()
    
    query = """
    MATCH path = shortestPath(
        (a:Character {name: $from_name, novel_id: $novel_id})-[*1..$max_depth]-(b:Character {name: $to_name, novel_id: $novel_id})
    )
    RETURN [node IN nodes(path) | node.name] as nodes,
           [rel IN relationships(path) | type(rel)] as relations
    """
    
    results = neo4j.run_query(query, {
        "from_name": from_name,
        "to_name": to_name,
        "novel_id": novel_id,
        "max_depth": max_depth
    })
    
    if results:
        return {
            "status": "SUCCESS",
            "data": results[0]
        }
    
    return {
        "status": "SUCCESS",
        "data": {
            "nodes": [],
            "relations": [],
            "message": "No path found"
        }
    }


# ============================================================
# 关系更新
# ============================================================

def update_relation(from_name: str, to_name: str, relation_type: str,
                    properties: dict = None, novel_id: str = None) -> dict:
    """更新角色关系"""
    novel_id = novel_id or settings.app.default_novel_id
    neo4j = get_neo4j()
    properties = properties or {}
    
    # 验证关系类型
    valid_relations = ["KILLED", "HATES", "LOVES", "ALLIED", "OWES", 
                       "MASTER_OF", "STUDENT_OF", "BELONGS_TO"]
    
    if relation_type.upper() not in valid_relations:
        return {
            "status": "FAILED",
            "error_code": "E103",
            "message": f"Invalid relation type: {relation_type}"
        }
    
    # 构建属性字符串
    props_str = ""
    if properties:
        props_items = [f"{k}: ${k}" for k in properties.keys()]
        props_str = " {" + ", ".join(props_items) + "}"
    
    query = f"""
    MATCH (a:Character {{name: $from_name, novel_id: $novel_id}})
    MATCH (b:Character {{name: $to_name, novel_id: $novel_id}})
    MERGE (a)-[r:{relation_type.upper()}{props_str}]->(b)
    RETURN a.name as from, b.name as to, type(r) as relation
    """
    
    params = {
        "from_name": from_name,
        "to_name": to_name,
        "novel_id": novel_id,
        **properties
    }
    
    results = neo4j.run_query(query, params)
    
    if results:
        return {
            "status": "SUCCESS",
            "message": f"Relation created: {from_name} -[{relation_type}]-> {to_name}"
        }
    
    return {
        "status": "FAILED",
        "error_code": "E101",
        "message": "One or both characters not found"
    }


def mark_dead(name: str, killer: str = None, chapter: int = None, 
              novel_id: str = None) -> dict:
    """标记角色死亡"""
    novel_id = novel_id or settings.app.default_novel_id
    neo4j = get_neo4j()
    
    # 更新状态为死亡
    query = """
    MATCH (c:Character {name: $name, novel_id: $novel_id})
    SET c.status = 'dead', c.death_chapter = $chapter
    RETURN c
    """
    
    neo4j.run_query(query, {"name": name, "novel_id": novel_id, "chapter": chapter})
    
    # 如果有凶手，创建 KILLED 关系
    if killer:
        update_relation(killer, name, "KILLED", {"chapter": chapter}, novel_id)
    
    return {
        "status": "SUCCESS",
        "message": f"{name} marked as dead" + (f" (killed by {killer})" if killer else "")
    }


def create_character_node(name: str, level: str = None, 
                          properties: dict = None, novel_id: str = None) -> dict:
    """创建新角色节点"""
    novel_id = novel_id or settings.app.default_novel_id
    neo4j = get_neo4j()
    properties = properties or {}
    
    query = """
    MERGE (c:Character {name: $name, novel_id: $novel_id})
    SET c.level = $level,
        c.status = 'alive'
    """
    
    # 添加额外属性
    for key, value in properties.items():
        query += f", c.{key} = ${key}"
    
    query += " RETURN c"
    
    params = {
        "name": name,
        "novel_id": novel_id,
        "level": level or "unknown",
        **properties
    }
    
    results = neo4j.run_query(query, params)
    
    return {
        "status": "SUCCESS",
        "message": f"Character node created: {name}"
    }


def batch_update_relations(changes: List[Dict], novel_id: str = None) -> dict:
    """批量更新关系"""
    novel_id = novel_id or settings.app.default_novel_id
    results = []
    
    for change in changes:
        from_name = change.get("from")
        to_name = change.get("to")
        relation = change.get("relation")
        properties = change.get("properties", {})
        
        if relation.upper() == "DEAD":
            result = mark_dead(to_name, from_name, properties.get("chapter"), novel_id)
        else:
            result = update_relation(from_name, to_name, relation, properties, novel_id)
        
        results.append(result)
    
    success_count = sum(1 for r in results if r.get("status") == "SUCCESS")
    
    return {
        "status": "SUCCESS",
        "data": {
            "total": len(changes),
            "success": success_count,
            "results": results
        }
    }


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Novel-Generate Graph Query")
    parser.add_argument("--action", required=True, help="Action to perform")
    parser.add_argument("--name", help="Character name")
    parser.add_argument("--from_name", help="Source character")
    parser.add_argument("--to_name", help="Target character")
    parser.add_argument("--relation", help="Relation type")
    parser.add_argument("--faction", help="Faction name")
    parser.add_argument("--novel_id", help="Novel ID")
    parser.add_argument("--level", help="Character level")
    parser.add_argument("--killer", help="Killer name")
    parser.add_argument("--chapter", type=int, help="Chapter number")
    parser.add_argument("--intensity", type=int, default=0, help="Min intensity")
    parser.add_argument("--changes", help="Batch changes (JSON array)")
    parser.add_argument("--properties", help="Additional properties (JSON)")
    
    args = parser.parse_args()
    novel_id = args.novel_id or settings.app.default_novel_id
    
    action_map = {
        "get_character": lambda: get_character(args.name, novel_id),
        "is_alive": lambda: is_alive(args.name, novel_id),
        "get_enemies": lambda: get_enemies(args.name, novel_id, args.intensity),
        "get_allies": lambda: get_allies(args.name, novel_id),
        "get_faction_members": lambda: get_faction_members(args.faction, novel_id),
        "find_path": lambda: find_path(args.from_name, args.to_name, novel_id),
        "update_relation": lambda: update_relation(
            args.from_name, args.to_name, args.relation,
            json.loads(args.properties) if args.properties else None,
            novel_id
        ),
        "mark_dead": lambda: mark_dead(args.name, args.killer, args.chapter, novel_id),
        "create_character": lambda: create_character_node(
            args.name, args.level,
            json.loads(args.properties) if args.properties else None,
            novel_id
        ),
        "batch_update": lambda: batch_update_relations(
            json.loads(args.changes), novel_id
        ),
    }
    
    if args.action in action_map:
        result = action_map[args.action]()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result.get("status") == "SUCCESS" else 1)
    else:
        print(json.dumps({"status": "FAILED", "message": f"Unknown action: {args.action}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
