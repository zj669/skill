#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志错误分析工具
用于解析 Maven/Java 项目的构建和测试日志，精确定位错误位置并生成分析报告。
解决 PowerShell 命令输出被截断的问题。
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


@dataclass
class ErrorEntry:
    """错误条目数据结构"""
    line_number: int
    error_type: str  # ERROR, FAILURE, EXCEPTION
    content: str
    context_lines: List[str]  # 错误后的上下文行
    stack_trace: List[str]  # 堆栈跟踪


class LogAnalyzer:
    """日志分析器"""
    
    # 错误模式定义
    ERROR_PATTERNS = {
        'maven_error': re.compile(r'\[ERROR\]'),
        'failure': re.compile(r'FAILURE|BUILD FAILURE|Test.*FAILED'),
        'exception': re.compile(r'Exception|Caused by:|at\s+\w+\.'),
        'compilation_error': re.compile(r'compilation failure|cannot find symbol|package.*does not exist'),
    }
    
    # 堆栈跟踪模式
    STACK_TRACE_PATTERN = re.compile(r'^\s+at\s+[\w\.$]+')
    CAUSED_BY_PATTERN = re.compile(r'^Caused by:')
    
    def __init__(self, log_path: str, max_errors: int = 5, context_lines: int = 20, encoding: Optional[str] = None):
        """
        初始化日志分析器
        
        Args:
            log_path: 日志文件路径
            max_errors: 最多提取的错误数量
            context_lines: 每个错误后提取的上下文行数
            encoding: 指定编码格式（可选，留空则自动检测）
        """
        self.log_path = Path(log_path)
        self.max_errors = max_errors
        self.context_lines = context_lines
        self.encoding = encoding  # 用户指定的编码
        self.detected_encoding: Optional[str] = None  # 检测到的编码
        self.errors: List[ErrorEntry] = []
        
    def _detect_encoding(self) -> str:
        """
        自动检测文件编码
        
        Returns:
            检测到的编码格式
        """
        # 如果用户指定了编码，直接使用
        if self.encoding:
            return self.encoding
        
        # 读取文件的前几行用于检测（前 10000 字节通常足够）
        try:
            with open(self.log_path, 'rb') as f:
                raw_data = f.read(10000)
            
            # 优先使用 chardet 库检测
            if CHARDET_AVAILABLE and raw_data:
                result = chardet.detect(raw_data)
                detected = result.get('encoding', 'utf-8')
                confidence = result.get('confidence', 0)
                
                # 如果置信度较高，使用检测结果
                if confidence > 0.7:
                    # 特殊处理：GB2312 和 GBK 都映射到 GBK（更广泛的兼容性）
                    if detected and detected.upper() in ['GB2312', 'GB18030']:
                        detected = 'GBK'
                    print(f"📝 检测到编码: {detected} (置信度: {confidence:.2%})")
                    return detected
            
            # 备用方案：尝试常用编码
            common_encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'utf-16']
            
            for enc in common_encodings:
                try:
                    raw_data.decode(enc)
                    print(f"📝 使用编码: {enc} (备用检测)")
                    return enc
                except (UnicodeDecodeError, LookupError):
                    continue
            
            # 如果所有方法都失败，使用 UTF-8 并忽略错误
            print(f"⚠️  无法确定编码，使用 UTF-8 (忽略错误)")
            return 'utf-8'
            
        except Exception as e:
            print(f"⚠️  编码检测失败: {e}，使用 UTF-8")
            return 'utf-8'
    
    def analyze(self) -> List[ErrorEntry]:
        """
        分析日志文件，提取错误信息
        支持自动编码检测（GBK、UTF-8、GB2312 等）
        
        Returns:
            错误条目列表
        """
        if not self.log_path.exists():
            raise FileNotFoundError(f"日志文件不存在: {self.log_path}")
        
        # 检测编码
        self.detected_encoding = self._detect_encoding()
        
        # 使用检测到的编码读取文件
        try:
            with open(self.log_path, 'r', encoding=self.detected_encoding, errors='replace') as f:
                lines = f.readlines()
        except Exception as e:
            # 如果读取失败，使用 UTF-8 并忽略错误
            print(f"⚠️  使用 {self.detected_encoding} 读取失败: {e}")
            print(f"📝 回退到 UTF-8 (忽略错误)")
            with open(self.log_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        
        i = 0
        while i < len(lines) and len(self.errors) < self.max_errors:
            line = lines[i]
            
            # 检查是否匹配错误模式
            error_type = self._identify_error_type(line)
            if error_type:
                # 提取上下文和堆栈跟踪
                context, stack_trace = self._extract_context(lines, i)
                
                error_entry = ErrorEntry(
                    line_number=i + 1,
                    error_type=error_type,
                    content=line.rstrip(),
                    context_lines=context,
                    stack_trace=stack_trace
                )
                self.errors.append(error_entry)
                
                # 跳过已经处理的上下文行
                i += len(context) + 1
            else:
                i += 1
        
        return self.errors
    
    def _identify_error_type(self, line: str) -> str:
        """识别错误类型"""
        if self.ERROR_PATTERNS['maven_error'].search(line):
            return 'ERROR'
        elif self.ERROR_PATTERNS['failure'].search(line):
            return 'FAILURE'
        elif self.CAUSED_BY_PATTERN.search(line):
            return 'EXCEPTION'
        return ''
    
    def _extract_context(self, lines: List[str], start_idx: int) -> Tuple[List[str], List[str]]:
        """
        提取错误的上下文和堆栈跟踪
        
        Args:
            lines: 所有日志行
            start_idx: 错误行的索引
            
        Returns:
            (上下文行列表, 堆栈跟踪列表)
        """
        context = []
        stack_trace = []
        
        # 提取后续行作为上下文
        for i in range(start_idx + 1, min(start_idx + 1 + self.context_lines, len(lines))):
            line = lines[i].rstrip()
            context.append(line)
            
            # 识别堆栈跟踪
            if self.STACK_TRACE_PATTERN.search(line) or self.CAUSED_BY_PATTERN.search(line):
                stack_trace.append(line)
            
            # 如果遇到空行或新的错误，停止提取
            if not line.strip():
                break
            if self._identify_error_type(line) and i > start_idx + 1:
                break
        
        return context, stack_trace
    
    def generate_report(self, output_path: str = None) -> str:
        """
        生成错误分析报告
        
        Args:
            output_path: 报告输出路径（可选）
            
        Returns:
            报告内容
        """
        if not self.errors:
            return "✅ 未发现错误！"
        
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
            
            if error.stack_trace:
                report_lines.extend([
                    "### 堆栈跟踪:",
                    *error.stack_trace,
                    ""
                ])
            
            if error.context_lines:
                report_lines.extend([
                    "### 上下文 (后续 {} 行):".format(len(error.context_lines)),
                    *error.context_lines[:10],  # 限制上下文行数避免过长
                    ""
                ])
            
            # 尝试提取关键信息
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
        
        # 如果指定了输出路径，写入文件
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✅ 报告已保存到: {output_file}")
        
        return report
    
    def _analyze_error(self, error: ErrorEntry) -> List[str]:
        """
        分析错误，提取关键信息
        
        Returns:
            分析结果行列表
        """
        analysis = []
        content = error.content + "\n" + "\n".join(error.context_lines)
        
        # 1. 检测编译错误 - 符号未找到
        if 'cannot find symbol' in content:
            analysis.append("❌ 错误类型: 符号未找到（编译错误）")
            symbol_match = re.search(r'symbol:\s+(\w+)\s+(\w+)', content)
            if symbol_match:
                symbol_type = symbol_match.group(1)
                symbol_name = symbol_match.group(2)
                analysis.append(f"   缺失符号: {symbol_type} {symbol_name}")
                
                # 提供修复建议
                if symbol_type == 'class':
                    analysis.append(f"💡 修复建议:")
                    analysis.append(f"   1. 检查是否缺少 import 语句")
                    analysis.append(f"   2. 确认类名拼写是否正确")
                    analysis.append(f"   3. 检查 Maven 依赖是否包含该类所在的包")
                elif symbol_type == 'method':
                    analysis.append(f"💡 修复建议:")
                    analysis.append(f"   1. 检查方法名拼写")
                    analysis.append(f"   2. 确认对象类型是否有该方法")
                    analysis.append(f"   3. 检查是否需要类型转换")
                elif symbol_type == 'variable':
                    analysis.append(f"💡 修复建议:")
                    analysis.append(f"   1. 检查变量是否已声明")
                    analysis.append(f"   2. 确认变量作用域是否正确")
        
        # 2. 检测包不存在
        if 'package' in content and 'does not exist' in content:
            analysis.append("❌ 错误类型: 包不存在（依赖缺失）")
            package_match = re.search(r'package\s+([\w.]+)', content)
            if package_match:
                package_name = package_match.group(1)
                analysis.append(f"   缺失包: {package_name}")
                analysis.append(f"💡 修复建议:")
                analysis.append(f"   1. 在 pom.xml 中添加对应的 Maven 依赖")
                analysis.append(f"   2. 执行 mvn clean install 重新构建")
                analysis.append(f"   3. 检查依赖版本是否兼容")
        
        # 3. 检测空指针异常
        if 'NullPointerException' in content or 'NPE' in content:
            analysis.append("❌ 错误类型: 空指针异常（运行时错误）")
            analysis.append(f"💡 修复建议:")
            analysis.append(f"   1. 检查对象是否已初始化")
            analysis.append(f"   2. 添加 null 检查或使用 Optional")
            analysis.append(f"   3. 对于 DDD 值对象，在构造函数中使用 Objects.requireNonNull()")
        
        # 4. 检测类型不匹配
        if 'incompatible types' in content or 'type mismatch' in content:
            analysis.append("❌ 错误类型: 类型不匹配（编译错误）")
            analysis.append(f"💡 修复建议:")
            analysis.append(f"   1. 检查变量声明类型与赋值类型是否一致")
            analysis.append(f"   2. 添加必要的类型转换")
            analysis.append(f"   3. 检查泛型类型参数")
        
        # 5. 检测测试失败
        if 'AssertionError' in content or 'expected' in content.lower() and 'but was' in content.lower():
            analysis.append("❌ 错误类型: 断言失败（测试错误）")
            analysis.append(f"💡 修复建议:")
            analysis.append(f"   1. 检查测试期望值是否正确")
            analysis.append(f"   2. 确认 Mock 对象的行为定义是否完整")
            analysis.append(f"   3. 验证测试数据是否符合业务规则")
        
        # 6. 检测 Lombok 相关问题
        if 'lombok' in content.lower():
            analysis.append("⚠️  可能涉及 Lombok 问题")
            analysis.append(f"💡 修复建议:")
            analysis.append(f"   1. 确认 IDE 已安装 Lombok 插件")
            analysis.append(f"   2. 启用 Annotation Processing")
            analysis.append(f"   3. 检查 Lombok 版本兼容性")
        
        # 7. 检测 MyBatis/Mapper 相关问题
        if 'mapper' in content.lower() or '@MapperScan' in content:
            analysis.append("⚠️  可能涉及 MyBatis Mapper 问题")
            analysis.append(f"💡 修复建议（DDD 项目）:")
            analysis.append(f"   1. 检查 @MapperScan 路径: com.example.*.infrastructure.persistence.mapper")
            analysis.append(f"   2. 确认 Mapper 接口位置是否正确")
            analysis.append(f"   3. 检查 XML 映射文件路径")
        
        # 8. 检测依赖注入问题
        if 'could not autowire' in content.lower() or 'no qualifying bean' in content.lower():
            analysis.append("❌ 错误类型: 依赖注入失败（配置错误）")
            analysis.append(f"💡 修复建议:")
            analysis.append(f"   1. 检查 @Component/@Service 注解是否存在")
            analysis.append(f"   2. 确认组件扫描路径是否正确")
            analysis.append(f"   3. 检查是否有循环依赖")
        
        # 9. 检测数据库连接问题
        if 'connection' in content.lower() and ('refused' in content.lower() or 'timeout' in content.lower()):
            analysis.append("❌ 错误类型: 数据库连接失败（环境错误）")
            analysis.append(f"💡 修复建议:")
            analysis.append(f"   1. 检查数据库是否已启动")
            analysis.append(f"   2. 验证 application.yml 中的连接配置")
            analysis.append(f"   3. 检查网络连接和防火墙设置")
        
        # 10. 提取文件位置
        file_match = re.search(r'\[(ERROR|WARNING)\]\s+([A-Za-z]:[\\/].*?\.java):\[(\d+)[,:](\d+)\]', content)
        if file_match:
            file_path = file_match.group(2)
            line_num = file_match.group(3)
            col_num = file_match.group(4)
            
            # 提取文件名（去掉路径）
            import os
            file_name = os.path.basename(file_path)
            
            analysis.append(f"📍 错误位置: {file_name}")
            analysis.append(f"   完整路径: {file_path}")
            analysis.append(f"   行列号: [{line_num}, {col_num}]")
            
            # DDD 分层检测
            if 'infrastructure' in file_path.lower():
                analysis.append(f"🏗️  DDD 层: 基础设施层")
            elif 'domain' in file_path.lower():
                analysis.append(f"🏗️  DDD 层: 领域层")
            elif 'application' in file_path.lower():
                analysis.append(f"🏗️  DDD 层: 应用层")
            elif 'interface' in file_path.lower() or 'controller' in file_path.lower():
                analysis.append(f"🏗️  DDD 层: 接口层")
        
        # 11. 检测异常类型
        exception_match = re.search(r'(\w+Exception|Error):', content)
        if exception_match and not any('错误类型' in line for line in analysis):
            exception_type = exception_match.group(1)
            analysis.append(f"⚠️  异常类型: {exception_type}")
        
        # 12. 检测 DDD 特定问题
        if 'aggregate' in content.lower() or 'entity' in content.lower() or 'valueobject' in content.lower():
            analysis.append(f"🎯 DDD 提示:")
            analysis.append(f"   检查领域模型的不变性约束和业务规则")
        
        return analysis
    
    def generate_bug_report(self) -> str:
        """
        生成简洁的 Bug 报告（按照文档中的格式）
        
        Returns:
            Bug 报告内容
        """
        if not self.errors:
            return "✅ 未发现错误！"
        
        # 只分析第一个错误（通常是根本原因）
        error = self.errors[0]
        content = error.content + "\n" + "\n".join(error.context_lines)
        
        # 确定错误类型
        failure_type = "Unknown"
        if 'cannot find symbol' in content:
            failure_type = "SymbolNotFound"
        elif 'package' in content and 'does not exist' in content:
            failure_type = "PackageNotFound"
        elif 'compilation failure' in content.lower():
            failure_type = "CompilationError"
        elif 'Exception' in content:
            failure_type = "RuntimeException"
        
        # 提取位置
        location = "Unknown"
        file_match = re.search(r'\[(ERROR|WARNING)\]\s+([A-Za-z]:[\\/].*?\.java):\[(\d+)[,:](\d+)\]', content)
        if file_match:
            file_path = Path(file_match.group(2))
            location = f"{file_path.name}:[{file_match.group(3)},{file_match.group(4)}]"
        
        # 提取关键跟踪
        key_trace = error.content
        if error.context_lines:
            key_trace += "\n" + "\n".join(error.context_lines[:5])
        
        # 生成报告
        report = f"""
> **[Bug Report]**
> * **Failure Type**: {failure_type}
> * **Location**: {location}
> * **Key Trace**:
> ```text
{key_trace}
> ```
> * **Root Cause**: {self._infer_root_cause(error)}
"""
        return report
    
    def _infer_root_cause(self, error: ErrorEntry) -> str:
        """推断根本原因"""
        content = error.content.lower()
        
        if 'cannot find symbol' in content:
            return "缺少类或包的导入，或者类名拼写错误"
        elif 'package' in content and 'does not exist' in content:
            return "Maven 依赖缺失或配置错误"
        elif 'compilation failure' in content:
            return "代码语法错误或类型不匹配"
        else:
            return "需要进一步分析"


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='日志错误分析工具 - 精确定位 Maven/Java 构建错误',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 分析日志并输出到控制台
  python log_analyzer.py -l path/to/build.log
  
  # 生成完整报告并保存
  python log_analyzer.py -l path/to/build.log -o path/to/report.md
  
  # 生成简洁的 Bug 报告
  python log_analyzer.py -l path/to/build.log --bug-report
  
  # 自定义错误数量和上下文行数
  python log_analyzer.py -l path/to/build.log -m 10 -c 30
        """
    )
    
    parser.add_argument('-l', '--log', required=True, help='日志文件路径')
    parser.add_argument('-o', '--output', help='报告输出路径（可选）')
    parser.add_argument('-m', '--max-errors', type=int, default=5, help='最多提取的错误数量（默认: 5）')
    parser.add_argument('-c', '--context-lines', type=int, default=20, help='每个错误的上下文行数（默认: 20）')
    parser.add_argument('-e', '--encoding', help='指定文件编码（如 utf-8, gbk, gb2312），留空则自动检测')
    parser.add_argument('--bug-report', action='store_true', help='生成简洁的 Bug 报告格式')
    parser.add_argument('--tail', type=int, help='如果没有找到错误，读取文件末尾指定行数')
    
    args = parser.parse_args()
    
    try:
        # 创建分析器
        analyzer = LogAnalyzer(
            log_path=args.log,
            max_errors=args.max_errors,
            context_lines=args.context_lines,
            encoding=args.encoding
        )
        
        # 分析日志
        print(f"🔍 正在分析日志: {args.log}")
        errors = analyzer.analyze()
        
        if errors:
            print(f"✅ 发现 {len(errors)} 个错误\n")
            
            # 生成报告
            if args.bug_report:
                report = analyzer.generate_bug_report()
            else:
                report = analyzer.generate_report(args.output)
            
            # 输出到控制台（如果没有指定输出文件）
            if not args.output:
                print(report)
        else:
            print("⚠️  未发现明显错误")
            
            # 备选策略：读取文件末尾
            if args.tail:
                print(f"\n📄 读取文件末尾 {args.tail} 行:\n")
                log_path = Path(args.log)
                # 使用检测到的编码
                detected_enc = analyzer.detected_encoding or 'utf-8'
                with open(log_path, 'r', encoding=detected_enc, errors='replace') as f:
                    lines = f.readlines()
                    tail_lines = lines[-args.tail:]
                    print("".join(tail_lines))
    
    except FileNotFoundError as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ 分析过程中出错: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
