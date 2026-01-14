"""
Novel-Generate 工具验证脚本
验证所有核心脚本的可用性 (包含数据写入和查询闭环)
"""

import subprocess
import json
import sys
import time
from pathlib import Path

# 脚本目录
SCRIPTS_DIR = Path(__file__).parent
CWD = str(SCRIPTS_DIR)


def run_script(script: str, args: list) -> dict:
    """运行脚本并返回结果"""
    cmd = [sys.executable, str(SCRIPTS_DIR / script)] + args
    print(f"\n{'='*60}")
    print(f"Running: python {script} {' '.join(args)}")
    print(f"{'='*60}")
    
    # 强制子进程使用 UTF-8 输出
    env = sys.modules['os'].environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=CWD,
            timeout=30,
            encoding='utf-8',
            errors='ignore',
            env=env
        )
        
        print(f"Exit Code: {result.returncode}")
        
        if result.stdout:
            print(f"Output:\n{result.stdout.strip()}")
        if result.stderr:
            print(f"Stderr:\n{result.stderr.strip()}")
        
        # 尝试解析 JSON 输出
        try:
            # 优先提取最后一行 JSON
            lines = result.stdout.strip().split('\n')
            json_str = ""
            for line in reversed(lines):
                if line.strip().startswith('{') and line.strip().endswith('}'):
                    json_str = line
                    break
            
            if json_str:
                data = json.loads(json_str)
                return {"success": result.returncode == 0, "data": data}
            else:
                # 尝试整个解析
                data = json.loads(result.stdout)
                return {"success": result.returncode == 0, "data": data}
                
        except json.JSONDecodeError:
            # 某些脚本可能只打印日志而不返回 JSON (如 db_connector)
            return {"success": result.returncode == 0, "raw": result.stdout}
    
    except subprocess.TimeoutExpired:
        print("ERROR: Command timed out")
        return {"success": False, "error": "timeout"}
    except Exception as e:
        print(f"ERROR: {e}")
        return {"success": False, "error": str(e)}


def test_state_manager():
    """测试状态管理器 (写入 -> 查询)"""
    print("\n" + "="*60)
    print("Phase 2: state_manager.py 测试")
    print("="*60)
    
    results = []
    
    # 2.0 初始化角色 (确保有数据)
    char_data = json.dumps({
        "name": "protagonist",
        "level": "练气一层",
        "inventory": ["新手礼包"],
        "skills": []
    }, ensure_ascii=False)
    results.append(("init_character", run_script("state_manager.py", ["--action", "init_character", "--json", char_data])))

    # 2.1 更新进度
    results.append(("update_progress", run_script("state_manager.py", ["--action", "update_progress", "--chapter", "1", "--status", "drafted"])))
    
    # 2.2 获取进度 (验证)
    results.append(("get_progress", run_script("state_manager.py", ["--action", "get_progress"])))
    
    # 2.3 更新背包
    results.append(("update_inventory", run_script("state_manager.py", ["--action", "update_inventory", "--add", json.dumps(["青锋剑"], ensure_ascii=False)])))
    
    # 2.4 更新情绪曲线
    results.append(("update_emo", run_script("state_manager.py", ["--action", "update_emo", "--score", "85"])))
    
    # 2.5 获取情绪曲线 (验证)
    results.append(("get_emo_curve", run_script("state_manager.py", ["--action", "get_emo_curve", "--count", "5"])))
    
    # 2.6 悬念管理 (添加)
    results.append(("update_hooks_add", run_script("state_manager.py", [
        "--action", "update_hooks",
        "--added", json.dumps(["神秘戒指的秘密", "老爷爷的身份"], ensure_ascii=False)
    ])))
    
    # 2.7 悬念管理 (查询验证)
    results.append(("get_hooks", run_script("state_manager.py", ["--action", "get_hooks"])))
    
    return results


def test_graph_query():
    """测试图谱查询 (创建 -> 关系 -> 查询)"""
    print("\n" + "="*60)
    print("Phase 3: graph_query.py 测试")
    print("="*60)
    
    results = []
    
    # 3.1 创建测试角色
    results.append(("create_char_A", run_script("graph_query.py", ["--action", "create_character", "--name", "测试主角", "--level", "练气一层"])))
    results.append(("create_char_B", run_script("graph_query.py", ["--action", "create_character", "--name", "测试反派", "--level", "练气三层"])))
    
    # 3.2 建立关系 (A HATES B)
    props = json.dumps({"intensity": 90}, ensure_ascii=False)
    results.append(("create_relation", run_script("graph_query.py", [
        "--action", "update_relation", 
        "--from_name", "测试主角", 
        "--to_name", "测试反派", 
        "--relation", "HATES",
        "--properties", props
    ])))
    
    # 3.3 验证仇人列表
    results.append(("get_enemies", run_script("graph_query.py", ["--action", "get_enemies", "--name", "测试主角"])))
    
    # 3.4 检查存活
    results.append(("is_alive", run_script("graph_query.py", ["--action", "is_alive", "--name", "测试主角"])))
    
    return results


def test_rag_engine():
    """测试 RAG 引擎 (入库 -> 查询)"""
    print("\n" + "="*60)
    print("Phase 4: rag_engine.py 测试")
    print("="*60)
    
    results = []
    
    # 4.1 入库测试数据
    test_text = "修仙界的基础境界分为：练气、筑基、金丹、元婴、化神。"
    results.append(("ingest", run_script("rag_engine.py", [
        "--action", "ingest", 
        "--text", test_text, 
        "--type", "test_knowledge"
    ])))
    
    # 等待索引刷新
    time.sleep(2)
    
    # 4.2 查询测试
    results.append(("query", run_script("rag_engine.py", ["--query", "修仙境界有哪些", "--top_k", "1"])))
    
    return results


def print_summary(all_results: dict):
    """打印测试摘要"""
    print("\n" + "="*60)
    print("Verification Summary (Write -> Read Loop)")
    print("="*60)
    
    total = 0
    passed = 0
    
    for phase, results in all_results.items():
        print(f"\n{phase}:")
        if isinstance(results, dict):
            results = [("test", results)]
        
        for name, result in results:
            total += 1
            status = "[PASS]" if result.get("success") else "[FAIL]"
            if result.get("success"):
                passed += 1
            print(f"  {name}: {status}")
            
            # 简单检查数据正确性
            data = result.get("data", {})
            if "data" in data and isinstance(data["data"], dict):
                # 如果有具体数据，可以打印关键摘要
                d = data["data"]
                if "current_chapter" in d:
                    print(f"    -> Chapter: {d['current_chapter']}")
                if "curve" in d:
                    print(f"    -> Curve Length: {len(d['curve'])}")
                if "hooks" in d:
                    print(f"    -> Hooks Count: {len(d['hooks'])}")
                if "enemies" in d:
                    print(f"    -> Enemies Found: {len(d['enemies'])}")
                if "results" in d and isinstance(d["results"], list):
                     print(f"    -> RAG Hits: {len(d['results'])}")
    
    print(f"\nTotal: {passed}/{total} Passed")
    return passed == total


if __name__ == "__main__":
    import os
    # 也可以在这里设置当前进程的 encoding，防止 print 报错
    # sys.stdout.reconfigure(encoding='utf-8') # Python 3.7+
    
    print("="*60)
    print("Novel-Generate Tool Verification (Mock Execution)")
    print("="*60)
    
    # 先测试数据库连接
    if not run_script("db_connector.py", []).get("success"):
        print("![FAIL] DB Connection Failed, aborting.")
        sys.exit(1)
    
    all_results = {}
    
    all_results["Phase 2: state_manager"] = test_state_manager()
    all_results["Phase 3: graph_query"] = test_graph_query()
    all_results["Phase 4: rag_engine"] = test_rag_engine()
    
    success = print_summary(all_results)
    
    sys.exit(0 if success else 1)
