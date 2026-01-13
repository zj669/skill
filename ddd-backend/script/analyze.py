#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志分析快速启动脚本
自动处理 .business 目录结构的路径问题

使用方法：
  python analyze.py {FeatureName} [日志文件名]
  
示例：
  python analyze.py Konwledage
  python analyze.py Konwledage Build_Phase2_UTF8_20260114002053.log
"""

import sys
import subprocess
from pathlib import Path

def main():
    """主函数"""
    # 显示帮助信息
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in ['-h', '--help', '/?']):
        print("=" * 70)
        print("🔧 日志分析快速启动脚本")
        print("=" * 70)
        print("\n使用方法：")
        print("  python analyze.py {FeatureName}")
        print("  python analyze.py {FeatureName} [日志文件名]")
        print("\n参数说明：")
        print("  FeatureName   : Feature 名称（必需），如 Konwledage")
        print("  日志文件名     : 可选，不指定则自动选择最新日志")
        print("\n示例：")
        print("  python analyze.py Konwledage")
        print("  python analyze.py Konwledage Build_Phase2_UTF8_20260114002053.log")
        print("\n提示：")
        print("  - 脚本会自动处理 .business 目录结构的路径")
        print("  - 报告自动保存到 .business/{FeatureName}/Bug_Report.md")
        print("  - 支持自动编码检测（GBK、UTF-8 等）")
        print("=" * 70)
        return
    
    if len(sys.argv) < 2:
        print("❌ 错误：缺少 Feature 名称")
        print("使用 'python analyze.py --help' 查看帮助")
        sys.exit(1)
    
    feature_name = sys.argv[1]
    
    # 计算路径（从脚本位置开始）
    script_dir = Path(__file__).parent.absolute()
    
    # 向上找到 .business 目录
    # 脚本在: .business/_Global_Protocols/ddd-backend/script/
    business_dir = script_dir.parent.parent.parent
    
    # Feature 目录
    feature_dir = business_dir / feature_name
    executelogs_dir = feature_dir / "executelogs"
    
    # 检查目录是否存在
    if not feature_dir.exists():
        print(f"❌ 错误：Feature 目录不存在: {feature_dir}")
        sys.exit(1)
    
    if not executelogs_dir.exists():
        print(f"❌ 错误：日志目录不存在: {executelogs_dir}")
        sys.exit(1)
    
    # 确定日志文件
    if len(sys.argv) >= 3:
        # 用户指定了日志文件名
        log_file_name = sys.argv[2]
        log_file = executelogs_dir / log_file_name
    else:
        # 自动查找最新的日志文件
        log_files = list(executelogs_dir.glob("*.log"))
        if not log_files:
            print(f"❌ 错误：未在 {executelogs_dir} 找到日志文件")
            sys.exit(1)
        
        # 按修改时间排序，取最新的
        log_file = max(log_files, key=lambda p: p.stat().st_mtime)
        print(f"📄 自动选择最新日志: {log_file.name}")
    
    # 检查日志文件是否存在
    if not log_file.exists():
        print(f"❌ 错误：日志文件不存在: {log_file}")
        sys.exit(1)
    
    # 报告输出路径
    report_file = feature_dir / "Bug_Report.md"
    
    # log_analyzer.py 的路径
    log_analyzer = script_dir / "log_analyzer.py"
    
    # 构建命令
    cmd = [
        "python",
        str(log_analyzer),
        "-l", str(log_file),
        "-o", str(report_file),
        "--bug-report"
    ]
    
    # 显示信息
    print("=" * 60)
    print(f"🔧 日志分析工具")
    print("=" * 60)
    print(f"Feature: {feature_name}")
    print(f"日志文件: {log_file.relative_to(business_dir)}")
    print(f"报告输出: {report_file.relative_to(business_dir)}")
    print("=" * 60)
    print()
    
    # 执行分析
    try:
        result = subprocess.run(cmd, check=True)
        print()
        print("=" * 60)
        print(f"✅ 分析完成！")
        print(f"📊 报告位置: {report_file}")
        print("=" * 60)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 分析失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
