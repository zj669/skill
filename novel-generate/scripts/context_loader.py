#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一上下文加载器 (Context Loader)
将多个分散的脚本调用整合为一次调用，返回完整的写作上下文
"""

import argparse
import json
import os
import sys
from typing import Dict, Any, Optional, List

# 复用现有模块
import state_manager
import rag_engine
import graph_query


class ContextLoader:
    """统一上下文加载器"""
    
    def __init__(self, project_dir: str = "."):
        self.project_dir = project_dir
        # state_manager, rag_engine, graph_query 均作为模块使用

    
    def _get_auto_mode(self) -> bool:
        """获取全自动模式状态"""
        try:
            status_file = os.path.join(self.project_dir, "project_status.json")
            if os.path.exists(status_file):
                with open(status_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("config", {}).get("auto_mode", False)
        except:
            pass
        return False



    def load_writing_context(self, chapter: int, characters: List[str] = None,
                             rag_queries: List[str] = None) -> Dict[str, Any]:
        """加载写作上下文"""
        context = {
            "chapter": chapter,
            "auto_mode": self._get_auto_mode(),
            "status": "SUCCESS",
            "data": {}
        }
        
        # 1. 基础状态
        try:
            progress = state_manager.get_progress().get("data", {})
            context["data"]["progress"] = progress
        except Exception as e:
            context["data"]["progress"] = {"error": str(e)}
        
        # 2. 上章尾部
        if chapter > 1:
            try:
                # 简化处理：读取上一章摘要
                summary = state_manager.get_chapter_summary(None, chapter - 1).get("data", "")
                context["data"]["previous_chapter_tail"] = summary[-500:] if summary else ""
            except Exception as e:
                context["data"]["previous_chapter_tail"] = {"error": str(e)}
        
        # 3. 活跃钩子
        try:
            hooks = state_manager.get_hooks().get("data", {}).get("hooks", [])
            context["data"]["active_hooks"] = hooks
        except Exception as e:
            context["data"]["active_hooks"] = {"error": str(e)}
            
        # 4. 情绪曲线
        try:
            emo = state_manager.get_emo_curve(count=5).get("data", {})
            context["data"]["emo_curve"] = emo.get("curve", [])
        except Exception as e:
            context["data"]["emo_curve"] = {"error": str(e)}
            
        # 5. 主角状态
        try:
            protagonist = state_manager.load_character("protagonist")
            context["data"]["protagonist"] = protagonist
        except Exception as e:
            context["data"]["protagonist"] = {"error": str(e)}
            
        # 6. 角色语音
        if characters:
            try:
                voices = {}
                for char_name in characters:
                    # 使用 load_character 代替 get_voice (state_manager里没有单独的get_voice函数)
                    # 虽然 CLI 有 get_voice，但它是组合逻辑。
                    # 其实 CLI 的 get_voice 是调用 load_character。
                    char_data = state_manager.load_character(char_name)
                    if "voice" in char_data:
                        voices[char_name] = char_data["voice"]
                context["data"]["character_voices"] = voices
            except Exception as e:
                context["data"]["character_voices"] = {"error": str(e)}
        
        # 7. RAG检索
        if rag_queries:
            try:
                rag_results = {}
                for query in rag_queries:
                    # 使用 rag_engine 模块函数
                    res = rag_engine.query_rag(query, top_k=3)
                    if res.get("status") == "SUCCESS":
                         rag_results[query] = res.get("data", {}).get("results", [])
                    else:
                         rag_results[query] = []
                context["data"]["rag_references"] = rag_results
            except Exception as e:
                context["data"]["rag_references"] = {"error": str(e)}
        
        # 8. 关系图
        # if characters: (暂略过 graph)
        
        return context

    def load_planning_context(self, chapter: int) -> Dict[str, Any]:
        """加载规划上下文"""
        context = {
            "chapter": chapter,
            "auto_mode": self._get_auto_mode(),
            "status": "SUCCESS",
            "data": {}
        }
        
        # 1. 上一章摘要
        if chapter > 1:
            try:
                summary = state_manager.get_chapter_summary(None, chapter - 1).get("data", "")
                context["data"]["last_summary"] = summary
            except Exception as e:
                context["data"]["last_summary"] = {"error": str(e)}
        
        # 2. 情绪曲线
        try:
            emo = state_manager.get_emo_curve(count=5).get("data", {})
            context["data"]["emo_curve"] = emo.get("curve", [])
        except Exception as e:
            context["data"]["emo_curve"] = {"error": str(e)}
            
        # 3. 活跃钩子
        try:
            hooks = state_manager.get_hooks().get("data", {}).get("hooks", [])
            context["data"]["hooks"] = hooks
        except Exception as e:
            context["data"]["hooks"] = {"error": str(e)}
            
        # 4. 主角状态
        try:
            protagonist = state_manager.load_character("protagonist")
            context["data"]["protagonist"] = protagonist
        except Exception as e:
            context["data"]["protagonist"] = {"error": str(e)}
            
        # 5. 卷级规划信息 (关键修改：读取文件)
        try:
            progress = state_manager.get_progress().get("data", {})
            vol_num = progress.get("current_volume", 1)
            
            vol_file = os.path.join(self.project_dir, "volumes", f"volume_{vol_num}", "outline.json")
            if os.path.exists(vol_file):
                with open(vol_file, "r", encoding="utf-8") as f:
                    context["data"]["volume_plan"] = json.load(f)
            else:
                context["data"]["volume_plan"] = {"warning": f"Volume outline not found: {vol_file}"}
        except Exception as e:
            context["data"]["volume_plan"] = {"error": str(e)}
        
        return context
    

    def load_settlement_context(self, chapter: int) -> Dict[str, Any]:
        """加载结算上下文"""
        context = {
            "chapter": chapter,
            "auto_mode": self._get_auto_mode(),
            "status": "SUCCESS",
            "data": {}
        }
        
        draft_path = os.path.join(self.project_dir, "drafts", f"chapter_{chapter}.md")
        
        # 1. 读取草稿
        if not os.path.exists(draft_path):
            context["data"]["draft_content"] = f"Error: Draft file not found at {draft_path}"
            return context
            
        try:
            with open(draft_path, "r", encoding="utf-8") as f:
                content = f.read()
            context["data"]["draft_content"] = content
            
            # 2. 解析元数据 (从文件末尾提取)
            # 格式: [KEY]: JSON_VALUE
            metadata = {}
            for line in content.splitlines()[::-1]: # 从后往前读
                line = line.strip()
                if line.startswith("[") and "]:" in line:
                    try:
                        key_part, val_part = line.split("]:", 1)
                        key = key_part[1:].strip()
                        val = json.loads(val_part.strip())
                        metadata[key] = val
                    except:
                        pass
                if len(metadata) >= 5: # 假设最多5个元数据字段，避免全读
                    break
            
            context["data"]["draft_metadata"] = metadata
            
        except Exception as e:
            context["data"]["draft_content"] = {"error": str(e)}
        
        # 3. 主角当前状态
        try:
            protagonist = state_manager.load_character("protagonist")
            context["data"]["protagonist_before"] = protagonist
        except Exception as e:
            context["data"]["protagonist_before"] = {"error": str(e)}
        
        return context


def main():
    parser = argparse.ArgumentParser(description="统一上下文加载器")
    parser.add_argument("--mode", "-m", required=True, 
                        choices=["writing", "planning", "settlement"],
                        help="上下文模式: writing(写作), planning(规划), settlement(结算)")
    parser.add_argument("--chapter", "-c", type=int, required=True, 
                        help="目标章节号")
    parser.add_argument("--characters", type=str, default=None,
                        help="角色列表(JSON格式), 如: '[\"叶凡\", \"老爷爷\"]'")
    parser.add_argument("--rag-queries", type=str, default=None,
                        help="RAG查询列表(JSON格式), 如: '[\"战斗描写\", \"功法特效\"]'")
    parser.add_argument("--project-dir", "-d", default=".", 
                        help="项目目录路径")
    parser.add_argument("--output-dir", "-o", default=None,
                        help="输出目录路径，结果将保存为 context.json")
    
    args = parser.parse_args()
    
    loader = ContextLoader(args.project_dir)
    
    # 解析JSON参数
    characters = json.loads(args.characters) if args.characters else None
    rag_queries = json.loads(args.rag_queries) if args.rag_queries else None
    
    # 根据模式加载上下文
    if args.mode == "writing":
        result = loader.load_writing_context(args.chapter, characters, rag_queries)
    elif args.mode == "planning":
        result = loader.load_planning_context(args.chapter)
    elif args.mode == "settlement":
        result = loader.load_settlement_context(args.chapter)
    else:
        result = {"status": "ERROR", "message": f"Unknown mode: {args.mode}"}
    
    # 添加时间戳
    from datetime import datetime
    result["timestamp"] = datetime.now().isoformat()
    
    # 输出到控制台
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 如果指定了输出目录，保存到文件
    if args.output_dir:
        os.makedirs(args.output_dir, exist_ok=True)
        output_file = os.path.join(args.output_dir, "context.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n📁 已保存到: {output_file}")


if __name__ == "__main__":
    main()

