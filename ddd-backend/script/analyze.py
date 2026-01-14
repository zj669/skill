#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志分析工具 (Standalone)
用于自动解析 Maven/Java 构建日志，精确定位错误位置并生成分析报告。

功能特点：
1. 自动检测文件编码（GBK, UTF-8等），解决 Windows 中文乱码问题
2. 智能识别 Maven 错误、编译失败、测试失败等多种错误类型
3. 生成 Bug_Report.md，包含关键堆栈和修复建议
4. 支持 Grep 模式，无需读取全文即可查看关键日志片段（防截断）

用法：
  # 生成分析报告 (标准模式)
  python analyze.py <日志路径> <报告路径>

  # 搜索关键字 (交互模式)
  python analyze.py <日志路径> --grep "NullPointerException" -c 10
"""

import re
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

# 尝试导入 chardet 用于编码检测
try:
    import chardet
    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False


def safe_print(msg: str, file=None):
    """
    安全打印函数，处理 Windows GBK 控制台无法显示 emoji 的问题
    """
    try:
        print(msg, file=file)
    except UnicodeEncodeError:
        import re
        clean_msg = re.sub(r'[^\x00-\x7F]+', '', msg)
        print(clean_msg, file=file)


@dataclass
class ErrorEntry:
    """错误条目数据结构"""
    line_number: int
    error_type: str
    content: str
    context_lines: List[str]
    stack_trace: List[str]


class LogAnalyzer:
    """日志分析器"""
    
    ERROR_PATTERNS = {
        'maven_error': re.compile(r'\[ERROR\]'),
        'failure': re.compile(r'FAILURE|BUILD FAILURE|Test.*FAILED'),
        'exception': re.compile(r'Exception|Caused by:|at\s+\w+\.'),
        'compilation_error': re.compile(r'compilation failure|cannot find symbol|package.*does not exist'),
    }
    
    STACK_TRACE_PATTERN = re.compile(r'^\s+at\s+[\w\.$]+')
    CAUSED_BY_PATTERN = re.compile(r'^Caused by:')
    
    def __init__(self, log_path: str, max_errors: int = 5, context_lines: int = 20, encoding: Optional[str] = None):
        self.log_path = Path(log_path)
        self.max_errors = max_errors
        self.context_lines = context_lines
        self.encoding = encoding
        self.detected_encoding: Optional[str] = None
        self.errors: List[ErrorEntry] = []
        
    def _detect_encoding(self) -> str:
        """自动检测文件编码"""
        if self.detected_encoding:
            return self.detected_encoding
            
        if self.encoding:
            self.detected_encoding = self.encoding
            return self.encoding
        
        try:
            with open(self.log_path, 'rb') as f:
                raw_data = f.read(10000)
            
            if CHARDET_AVAILABLE and raw_data:
                result = chardet.detect(raw_data)
                detected = result.get('encoding', 'utf-8')
                confidence = result.get('confidence', 0)
                
                if confidence > 0.7:
                    if detected and detected.upper() in ['GB2312', 'GB18030']:
                        detected = 'GBK'
                    safe_print(f"[*] 检测到编码: {detected} (置信度: {confidence:.2%})")
                    self.detected_encoding = detected
                    return detected
            
            # 备用检测
            common_encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'utf-16']
            for enc in common_encodings:
                try:
                    raw_data.decode(enc)
                    safe_print(f"[*] 使用编码: {enc} (备用检测)")
                    self.detected_encoding = enc
                    return enc
                except (UnicodeDecodeError, LookupError):
                    continue
            
            safe_print(f"[!] 无法确定编码，使用 UTF-8")
            self.detected_encoding = 'utf-8'
            return 'utf-8'
            
        except Exception as e:
            safe_print(f"[!] 编码检测失败: {e}，使用 UTF-8")
            self.detected_encoding = 'utf-8'
            return 'utf-8'

    def read_lines(self) -> List[str]:
        """读取所有行（使用检测到的编码），并标准化换行符"""
        if not self.log_path.exists():
            raise FileNotFoundError(f"日志文件不存在: {self.log_path}")
            
        encoding = self._detect_encoding()
        try:
            with open(self.log_path, 'rb') as f:
                raw_data = f.read()
            
            # 标准化换行符：有些日志（如 Maven 进度条）使用单独的 \r 或混合换行
            # 1. 先将 CRLF 转为 LF
            # 2. 再将剩余的单独 CR 转为 LF
            normalized = raw_data.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
            text = normalized.decode(encoding, errors='replace')
            lines = text.split('\n')
            
            # 保留尾部空行信息（与 readlines 行为一致）
            if lines and lines[-1] == '':
                lines = lines[:-1]
            
            return [line + '\n' for line in lines]
            
        except Exception as e:
            safe_print(f"[!] 读取失败: {e}，重试 UTF-8")
            with open(self.log_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.readlines()

    def analyze(self) -> List[ErrorEntry]:
        """分析日志文件"""
        lines = self.read_lines()
        
        i = 0
        while i < len(lines) and len(self.errors) < self.max_errors:
            line = lines[i]
            if self._identify_error_type(line):
                context, stack_trace = self._extract_context(lines, i)
                error_entry = ErrorEntry(
                    line_number=i + 1,
                    error_type=self._identify_error_type(line),
                    content=line.rstrip(),
                    context_lines=context,
                    stack_trace=stack_trace
                )
                self.errors.append(error_entry)
                i += len(context) + 1
            else:
                i += 1
        return self.errors

    def grep_search(self, keyword: str, max_matches: int = 10):
        """
        搜索关键字并打印上下文（前后各 context_lines 行）
        """
        lines = self.read_lines()
        total_lines = len(lines)
        safe_print(f"[*] 正在搜索: '{keyword}' (上下文: 前后各 {self.context_lines} 行, 最大匹配: {max_matches})")
        safe_print(f"[*] 日志文件共 {total_lines} 行")
        safe_print("")
        
        matches_found = 0
        matched_ranges = set()  # 记录已输出的行号范围，避免重复
        
        i = 0
        while i < total_lines and matches_found < max_matches:
            if keyword in lines[i] and i not in matched_ranges:
                matches_found += 1
                
                # 计算前后上下文范围
                start = max(0, i - self.context_lines)
                end = min(total_lines, i + self.context_lines + 1)
                
                safe_print("=" * 70)
                safe_print(f"匹配 #{matches_found} @ 行 {i+1}")
                safe_print("-" * 70)
                
                # 打印前文
                for j in range(start, i):
                    if j not in matched_ranges:
                        safe_print(f"  {j+1:5d} | {lines[j].rstrip()}")
                        matched_ranges.add(j)
                
                # 打印匹配行（高亮）
                safe_print(f"> {i+1:5d} | {lines[i].rstrip()}")
                matched_ranges.add(i)
                
                # 打印后文
                for j in range(i + 1, end):
                    if j not in matched_ranges:
                        safe_print(f"  {j+1:5d} | {lines[j].rstrip()}")
                        matched_ranges.add(j)
                
                safe_print("")
                
                # 跳过已打印的后文范围，避免重复匹配
                i = end
            else:
                i += 1
        
        if matches_found == 0:
            safe_print("[!] 未找到匹配项")
        else:
            safe_print("=" * 70)
            safe_print(f"[*] 搜索完成，共找到 {matches_found} 处匹配")

    def _identify_error_type(self, line: str) -> str:
        if self.ERROR_PATTERNS['maven_error'].search(line):
            return 'ERROR'
        elif self.ERROR_PATTERNS['failure'].search(line):
            return 'FAILURE'
        elif self.CAUSED_BY_PATTERN.search(line):
            return 'EXCEPTION'
        return ''
    
    def _extract_context(self, lines: List[str], start_idx: int) -> Tuple[List[str], List[str]]:
        context = []
        stack_trace = []
        for i in range(start_idx + 1, min(start_idx + 1 + self.context_lines, len(lines))):
            line = lines[i].rstrip()
            context.append(line)
            if self.STACK_TRACE_PATTERN.search(line) or self.CAUSED_BY_PATTERN.search(line):
                stack_trace.append(line)
            if not line.strip():
                break
            if self._identify_error_type(line) and i > start_idx + 1:
                break
        return context, stack_trace
    
    def generate_report(self, output_path: str = None) -> str:
        """生成详细报告"""
        if not self.errors:
            return "[OK] 未发现错误！"
        
        report_lines = [
            "=" * 80,
            f"错误日志分析报告",
            f"日志文件: {self.log_path}",
            f"文件编码: {self.detected_encoding or '未检测'}",
            f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"发现错误: {len(self.errors)} 个",
            "=" * 80,
            ""
        ]
        
        for idx, error in enumerate(self.errors, 1):
            report_lines.extend([
                f"## 错误 #{idx}: {error.error_type}",
                f"位置: 第 {error.line_number} 行",
                "-" * 80,
                "### 错误内容:",
                error.content,
                ""
            ])
            if error.context_lines:
                report_lines.extend([
                    "### 上下文:",
                    *error.context_lines[:10],
                    ""
                ])
            analysis = self._analyze_error(error)
            if analysis:
                report_lines.extend([
                    "### 错误分析:",
                    *analysis,
                    ""
                ])
            report_lines.append("=" * 80)
            report_lines.append("")
        
        report = "\n".join(report_lines)
        if output_path:
            self._save_report(report, output_path)
        return report

    def generate_bug_report(self) -> str:
        """生成简洁 Bug 报告"""
        if not self.errors:
            return "[OK] 未发现错误！"
        
        error = self.errors[0]
        content = error.content + "\n" + "\n".join(error.context_lines)
        
        failure_type = "Unknown"
        if 'cannot find symbol' in content: failure_type = "SymbolNotFound"
        elif 'package' in content and 'does not exist' in content: failure_type = "PackageNotFound"
        elif 'compilation failure' in content.lower(): failure_type = "CompilationError"
        elif 'Exception' in content: failure_type = "RuntimeException"
        
        location = "Unknown"
        file_match = re.search(r'\[(ERROR|WARNING)\]\s+([A-Za-z]:[\\/].*?\.java):\[(\d+)[,:](\d+)\]', content)
        if file_match:
            location = f"{Path(file_match.group(2)).name}:[{file_match.group(3)},{file_match.group(4)}]"
            
        key_trace = error.content
        if error.context_lines:
            key_trace += "\n" + "\n".join(error.context_lines[:5])
            
        return f"""
> **[Bug Report]**
> * **Failure Type**: {failure_type}
> * **Location**: {location}
> * **Key Trace**:
> ```text
{key_trace}
> ```
> * **Root Cause**: {self._infer_root_cause(error)}
"""

    def _analyze_error(self, error: ErrorEntry) -> List[str]:
        analysis = []
        content = error.content + "\n" + "\n".join(error.context_lines)
        
        if 'cannot find symbol' in content:
            analysis.append("[X] 错误类型: 符号未找到")
            analysis.append("[*] 修复建议: 检查 import、拼写或依赖")
        elif 'package' in content and 'does not exist' in content:
            analysis.append("[X] 错误类型: 包不存在")
            analysis.append("[*] 修复建议: 检查 Maven 依赖")
        elif 'NullPointerException' in content:
            analysis.append("[X] 错误类型: 空指针异常")
        elif 'incompatible types' in content:
            analysis.append("[X] 错误类型: 类型不匹配")
        
        file_match = re.search(r'\[(ERROR|WARNING)\]\s+([A-Za-z]:[\\/].*?\.java):\[(\d+)[,:](\d+)\]', content)
        if file_match:
            analysis.append(f"[*] 位置: {Path(file_match.group(2)).name}:[{file_match.group(3)},{file_match.group(4)}]")
            
        return analysis

    def _infer_root_cause(self, error: ErrorEntry) -> str:
        content = error.content.lower()
        if 'cannot find symbol' in content: return "缺少类/包导入或拼写错误"
        elif 'package' in content: return "Maven 依赖缺失"
        return "代码语法错误或逻辑异常"

    def _save_report(self, report: str, path: str):
        output_file = Path(path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        safe_print(f"[+] 报告已保存到: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Java/Maven 日志分析与搜索工具')
    parser.add_argument('log_path', help='日志文件路径')
    parser.add_argument('report_path', nargs='?', help='报告输出路径 (仅在分析模式下需要)')
    parser.add_argument('--grep', help='搜索关键字 (Grep 模式)')
    parser.add_argument('-c', '--context', type=int, default=20, help='上下文行数 (默认: 20)')
    parser.add_argument('-n', '--max-matches', type=int, default=10, help='最大匹配数量 (默认: 10，防止输出过多)')
    
    args = parser.parse_args()
    
    log_path = Path(args.log_path).absolute()
    if not log_path.exists():
        safe_print(f"[X] 错误: 日志文件不存在 {log_path}")
        sys.exit(1)

    try:
        analyzer = LogAnalyzer(str(log_path), context_lines=args.context)
        
        # 模式 1: Grep 搜索 (交互模式)
        if args.grep:
            analyzer.grep_search(args.grep, max_matches=args.max_matches)
            return

        # 模式 2: 完整分析 (报告模式)
        if not args.report_path:
            # 如果没有 grep 也没有 report_path，提示错误
            safe_print("[!] 必须指定报告输出路径，或使用 --grep 进行搜索")
            print("用法: python analyze.py <日志路径> <报告路径>")
            sys.exit(1)
            
        report_path = Path(args.report_path).absolute()
        safe_print(f"[*] 正在分析日志: {log_path.name}")
        errors = analyzer.analyze()
        
        if errors:
            safe_print(f"[+] 发现 {len(errors)} 个错误\n")
            report = analyzer.generate_bug_report()
            analyzer._save_report(report, str(report_path))
            print("\n" + report + "\n")
        else:
            safe_print("[!] 未发现明显错误")
            
    except Exception as e:
        safe_print(f"[X] 执行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
