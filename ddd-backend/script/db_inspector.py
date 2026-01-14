#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库结构检查工具 (Explicit Mode)
用于连接数据库并生成表结构报告。
必须显式提供数据库连接参数，不依赖项目配置文件。
"""

import sys
import argparse
from pathlib import Path
from typing import Optional
from datetime import datetime

try:
    import pymysql
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False


class DatabaseInspector:
    """数据库检查器"""
    
    def __init__(self, host: str, port: int, database: str, username: str, password: str):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.connection = None
    
    def connect(self) -> bool:
        """连接数据库"""
        if not PYMYSQL_AVAILABLE:
            print("❌ 错误: 需要安装 pymysql。请执行: pip install pymysql")
            return False
        
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.username,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                connect_timeout=10
            )
            return True
        except pymysql.Error as e:
            print(f"❌ 数据库连接失败: {e}")
            return False
    
    def get_tables(self) -> list:
        """获取所有表名"""
        with self.connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            return [row[0] for row in cursor.fetchall()]
    
    def get_table_ddl(self, table_name: str) -> str:
        """获取表的 DDL"""
        with self.connection.cursor() as cursor:
            cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
            result = cursor.fetchone()
            return result[1] if result else ""
    
    def get_table_columns(self, table_name: str) -> list:
        """获取表的列信息"""
        with self.connection.cursor() as cursor:
            cursor.execute(f"DESCRIBE `{table_name}`")
            return cursor.fetchall()
    
    def close(self):
        """关闭连接"""
        if self.connection:
            self.connection.close()
    
    def generate_report(self, output_path: Optional[Path] = None) -> str:
        """生成数据库结构报告"""
        tables = self.get_tables()
        
        lines = [
            "=" * 80,
            "📊 数据库结构报告",
            f"数据库: {self.database}",
            f"主机: {self.host}:{self.port}",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"表数量: {len(tables)}",
            "=" * 80,
            ""
        ]
        
        for table in tables:
            lines.append(f"## 📋 表: {table}")
            lines.append("-" * 40)
            
            # 列信息
            columns = self.get_table_columns(table)
            lines.append("### 字段列表:")
            lines.append("| 字段名 | 类型 | 可空 | 键 | 默认值 | 备注 |")
            lines.append("|--------|------|------|-----|--------|------|")
            for col in columns:
                field, type_, null, key, default, extra = col
                lines.append(f"| {field} | {type_} | {null} | {key or ''} | {default or ''} | {extra or ''} |")
            
            lines.append("")
            
            # DDL
            lines.append("### DDL:")
            lines.append("```sql")
            lines.append(self.get_table_ddl(table))
            lines.append("```")
            lines.append("")
            lines.append("=" * 80)
            lines.append("")
        
        report = "\n".join(lines)
        
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✅ 报告已保存到: {output_path}")
        
        return report


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='数据库结构检查工具 (Explicit Mode) - 必须显式提供连接参数',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 打印到控制台
  python db_inspector.py --host localhost --user root --password 123456 --database mydb

  # 输出到文件
  python db_inspector.py --host 192.168.1.10 --user admin --password secret --database production -o report.md
        """
    )
    
    # 必需参数
    required_group = parser.add_argument_group('Required Arguments')
    required_group.add_argument('--host', required=True, help='数据库主机 (e.g., localhost)')
    required_group.add_argument('--user', required=True, help='数据库用户名')
    required_group.add_argument('--password', required=True, help='数据库密码')
    required_group.add_argument('--database', required=True, help='目标数据库名')
    
    # 可选参数
    parser.add_argument('--port', type=int, default=3306, help='数据库端口 (默认: 3306)')
    parser.add_argument('-o', '--output', help='报告输出路径 (可选)')
    
    args = parser.parse_args()
    
    # 连接并检查
    inspector = DatabaseInspector(args.host, args.port, args.database, args.user, args.password)
    
    if not inspector.connect():
        sys.exit(1)
    
    try:
        print(f"✅ 数据库连接成功: {args.host}:{args.port}/{args.database}")
        
        output_path = Path(args.output) if args.output else None
        report = inspector.generate_report(output_path)
        
        if not output_path:
            print("\n" + report)
    finally:
        inspector.close()


if __name__ == '__main__':
    main()
