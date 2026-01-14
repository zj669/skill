#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
章节连贯性检查脚本
检查相邻章节之间的时间、空间、情绪连贯性
"""

import argparse
import os
import re
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class ContinuityType(Enum):
    """连贯性检查类型"""
    TIME = "时间连续性"
    SPACE = "空间连续性"
    EMOTION = "情绪连续性"
    CHARACTER = "人物连续性"


@dataclass
class ContinuityIssue:
    """连贯性问题"""
    issue_type: ContinuityType
    severity: str  # WARNING, ERROR
    description: str
    prev_context: str
    curr_context: str
    suggestion: str


class ContinuityChecker:
    """章节连贯性检查器"""
    
    # 时间跳跃词汇
    TIME_JUMP_PATTERNS = [
        (r"翌日|第二天|次日", "日间跳跃"),
        (r"数日后|几天后|多日后", "多日跳跃"),
        (r"一月后|一年后|数月后", "长期跳跃"),
        (r"清晨|早上|黎明", "时段-清晨"),
        (r"正午|中午", "时段-正午"),
        (r"傍晚|黄昏|日落", "时段-傍晚"),
        (r"夜晚|深夜|子时", "时段-夜晚"),
    ]
    
    # 空间指示词
    SPACE_PATTERNS = [
        r"山门|山峰|洞府|密室",
        r"城中|城外|街道|酒楼",
        r"森林|荒野|沙漠|海边",
        r"阵法|禁地|秘境|古迹",
    ]
    
    # 情绪词汇
    EMOTION_PATTERNS = {
        "紧张": [r"紧张|焦虑|担忧|惶恐", r"心跳加速|手心冒汗|呼吸急促"],
        "愤怒": [r"愤怒|暴怒|狂怒", r"青筋暴起|怒目圆睁|杀意"],
        "平静": [r"平静|安宁|祥和", r"盘膝|打坐|修炼"],
        "喜悦": [r"喜悦|高兴|兴奋", r"嘴角上扬|眼含笑意"],
        "悲伤": [r"悲伤|痛苦|悲痛", r"泪流|哽咽|心如刀绞"],
    }
    
    def __init__(self, drafts_dir: str = "drafts"):
        self.drafts_dir = drafts_dir
        self.issues: List[ContinuityIssue] = []
    
    def load_chapter(self, chapter_num: int) -> Optional[str]:
        """加载章节内容"""
        patterns = [
            f"chapter_{chapter_num}.md",
            f"chapter_{chapter_num}_polished.md",
            f"第{chapter_num}章.md",
        ]
        
        for pattern in patterns:
            path = os.path.join(self.drafts_dir, pattern)
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
        return None
    
    def get_tail(self, content: str, chars: int = 500) -> str:
        """获取章节尾部内容"""
        # 去除元数据部分
        if "<!-- 元数据" in content:
            content = content.split("<!-- 元数据")[0]
        return content[-chars:] if len(content) > chars else content
    
    def get_head(self, content: str, chars: int = 500) -> str:
        """获取章节开头内容"""
        # 跳过标题行
        lines = content.split('\n')
        start_idx = 0
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith('#'):
                start_idx = i
                break
        text = '\n'.join(lines[start_idx:])
        return text[:chars] if len(text) > chars else text
    
    def detect_time_state(self, text: str) -> Dict[str, str]:
        """检测文本中的时间状态"""
        result = {"period": None, "jump": None}
        
        for pattern, label in self.TIME_JUMP_PATTERNS:
            if re.search(pattern, text):
                if "跳跃" in label:
                    result["jump"] = label
                else:
                    result["period"] = label
        return result
    
    def detect_emotion_state(self, text: str) -> str:
        """检测文本中的情绪状态"""
        emotion_scores = {}
        
        for emotion, patterns in self.EMOTION_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, text)
                score += len(matches)
            emotion_scores[emotion] = score
        
        if not any(emotion_scores.values()):
            return "未知"
        return max(emotion_scores, key=emotion_scores.get)
    
    def check_time_continuity(self, prev_tail: str, curr_head: str) -> Optional[ContinuityIssue]:
        """检查时间连续性"""
        prev_time = self.detect_time_state(prev_tail)
        curr_time = self.detect_time_state(curr_head)
        
        # 检查是否有未交代的时间跳跃
        if curr_time["jump"]:
            # 检查开头100字是否有过渡
            first_100 = curr_head[:100]
            if not re.search(r"过去了|已经|时间|经过", first_100):
                return ContinuityIssue(
                    issue_type=ContinuityType.TIME,
                    severity="WARNING",
                    description=f"检测到{curr_time['jump']}，但开头缺少过渡描写",
                    prev_context=prev_tail[-100:],
                    curr_context=curr_head[:100],
                    suggestion="在开头添加时间过渡语，如「不知过了多久」或删除时间跳跃词"
                )
        
        # 检查时段突变
        if prev_time["period"] and curr_time["period"]:
            if prev_time["period"] == "时段-夜晚" and curr_time["period"] == "时段-清晨":
                first_150 = curr_head[:150]
                if not re.search(r"一夜|天亮|醒来|睁眼", first_150):
                    return ContinuityIssue(
                        issue_type=ContinuityType.TIME,
                        severity="WARNING",
                        description="从夜晚跳转到清晨，缺少过渡",
                        prev_context=prev_tail[-100:],
                        curr_context=curr_head[:100],
                        suggestion="添加入睡/醒来的过渡描写"
                    )
        return None
    
    def check_emotion_continuity(self, prev_tail: str, curr_head: str) -> Optional[ContinuityIssue]:
        """检查情绪连续性"""
        prev_emotion = self.detect_emotion_state(prev_tail)
        curr_emotion = self.detect_emotion_state(curr_head[:200])
        
        # 情绪突变检测
        incompatible = {
            ("紧张", "平静"),
            ("愤怒", "喜悦"),
            ("悲伤", "喜悦"),
        }
        
        if (prev_emotion, curr_emotion) in incompatible or (curr_emotion, prev_emotion) in incompatible:
            return ContinuityIssue(
                issue_type=ContinuityType.EMOTION,
                severity="WARNING",
                description=f"情绪突变: 上章「{prev_emotion}」→ 本章「{curr_emotion}」",
                prev_context=prev_tail[-100:],
                curr_context=curr_head[:100],
                suggestion="添加情绪过渡描写，或调整开篇情绪基调"
            )
        return None
    
    def check(self, current_chapter: int, previous_chapter: int = None) -> List[ContinuityIssue]:
        """执行连贯性检查"""
        if previous_chapter is None:
            previous_chapter = current_chapter - 1
        
        if previous_chapter < 1:
            print(f"跳过第{current_chapter}章检查：无前置章节")
            return []
        
        prev_content = self.load_chapter(previous_chapter)
        curr_content = self.load_chapter(current_chapter)
        
        if not prev_content:
            print(f"警告: 无法加载第{previous_chapter}章")
            return []
        if not curr_content:
            print(f"警告: 无法加载第{current_chapter}章")
            return []
        
        prev_tail = self.get_tail(prev_content)
        curr_head = self.get_head(curr_content)
        
        self.issues = []
        
        # 执行各项检查
        time_issue = self.check_time_continuity(prev_tail, curr_head)
        if time_issue:
            self.issues.append(time_issue)
        
        emotion_issue = self.check_emotion_continuity(prev_tail, curr_head)
        if emotion_issue:
            self.issues.append(emotion_issue)
        
        return self.issues
    
    def print_report(self):
        """打印检查报告"""
        if not self.issues:
            print("✅ 连贯性检查通过，未发现问题")
            return
        
        print(f"\n⚠️ 发现 {len(self.issues)} 个连贯性问题:\n")
        print("=" * 60)
        
        for i, issue in enumerate(self.issues, 1):
            severity_icon = "🔴" if issue.severity == "ERROR" else "🟡"
            print(f"\n{severity_icon} 问题 {i}: [{issue.issue_type.value}]")
            print(f"   描述: {issue.description}")
            print(f"   上章尾: ...{issue.prev_context[-50:]}")
            print(f"   本章头: {issue.curr_context[:50]}...")
            print(f"   建议: {issue.suggestion}")
        
        print("\n" + "=" * 60)
    
    def to_json(self) -> str:
        """输出JSON格式报告"""
        result = {
            "status": "PASS" if not self.issues else "WARNING",
            "issue_count": len(self.issues),
            "issues": [
                {
                    "type": issue.issue_type.value,
                    "severity": issue.severity,
                    "description": issue.description,
                    "suggestion": issue.suggestion,
                }
                for issue in self.issues
            ]
        }
        return json.dumps(result, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="章节连贯性检查")
    parser.add_argument("--current", "-c", type=int, required=True, help="当前章节号")
    parser.add_argument("--previous", "-p", type=int, help="上一章节号(默认: current-1)")
    parser.add_argument("--drafts-dir", "-d", default="drafts", help="草稿目录路径")
    parser.add_argument("--output-dir", "-o", default=None, help="输出目录路径")
    parser.add_argument("--json", action="store_true", help="输出JSON格式")
    
    args = parser.parse_args()
    
    checker = ContinuityChecker(drafts_dir=args.drafts_dir)
    checker.check(args.current, args.previous)
    
    if args.json:
        print(checker.to_json())
    else:
        checker.print_report()
    
    # 如果指定了输出目录，保存到文件
    if args.output_dir:
        import os
        from datetime import datetime
        os.makedirs(args.output_dir, exist_ok=True)
        output_file = os.path.join(args.output_dir, "continuity.json")
        
        result = json.loads(checker.to_json())
        result["timestamp"] = datetime.now().isoformat()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n📁 已保存到: {output_file}")


if __name__ == "__main__":
    main()
