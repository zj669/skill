#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库结构检查工具
用于连接数据库并生成表结构报告，支持从 Spring Boot 配置文件读取连接参数。
"""

import re
import sys
import argparse
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime

# 尝试导入依赖
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    import pymysql
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False


class ConfigParser:
    """Spring Boot 配置文件解析器"""
    
    @staticmethod
    def find_config_file(project_root: Path, profile: Optional[str] = None) -> Optional[Path]:
        """
        查找配置文件
        优先级: application-{profile}.yml > application.yml > application.properties
        """
        resources_dir = project_root / "src" / "main" / "resources"
        
        if not resources_dir.exists():
            return None
        
        # 按优先级查找
        candidates = []
        if profile:
            candidates.append(resources_dir / f"application-{profile}.yml")
            candidates.append(resources_dir / f"application-{profile}.yaml")
            candidates.append(resources_dir / f"application-{profile}.properties")
        
        candidates.extend([
            resources_dir / "application.yml",
            resources_dir / "application.yaml",
            resources_dir / "application.properties",
        ])
        
        for candidate in candidates:
            if candidate.exists():
                return candidate
        
        return None
    
    @staticmethod
    def parse_yaml_config(config_path: Path) -> Dict:
        """解析 YAML 配置文件"""
        if not YAML_AVAILABLE:
            raise ImportError("需要安装 pyyaml: pip install pyyaml")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    @staticmethod
    def parse_properties_config(config_path: Path) -> Dict:
        """解析 properties 配置文件"""
        config = {}
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # 将 a.b.c=value 转换为嵌套字典
                    keys = key.strip().split('.')
                    current = config
                    for k in keys[:-1]:
                        current = current.setdefault(k, {})
                    current[keys[-1]] = value.strip()
        return config
    
    @staticmethod
    def extract_db_config(config: Dict) -> Tuple[str, str, str, str, int]:
        """
        从配置中提取数据库连接参数
        
        Returns:
            (host, port, database, username, password)
        """
        # 获取 datasource 配置
        datasource = config.get('spring', {}).get('datasource', {})
        
        url = datasource.get('url', '')
        username = datasource.get('username', '')
        password = datasource.get('password', '')
        
        # 解析 JDBC URL: jdbc:mysql://host:port/database?params
        pattern = r'jdbc:mysql://([^:/]+):?(\d+)?/([^?]+)'
        match = re.search(pattern, url)
        
        if match:
            host = match.group(1)
            port = int(match.group(2)) if match.group(2) else 3306
            database = match.group(3)
        else:
            host, port, database = 'localhost', 3306, ''
        
        return host, port, database, username, password


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
            raise ImportError("需要安装 pymysql: pip install pymysql")
        
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
        description='数据库结构检查工具 - 从 Spring Boot 配置读取连接并生成表结构报告',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 自动读取项目配置
  python db_inspector.py -p /path/to/project
  
  # 指定环境 profile
  python db_inspector.py -p /path/to/project --profile dev
  
  # 手动指定连接参数
  python db_inspector.py --host localhost --port 3306 --database mydb --user root --password 123456
  
  # 输出到文件
  python db_inspector.py -p /path/to/project -o db_report.md
        """
    )
    
    parser.add_argument('-p', '--project', help='项目根目录路径')
    parser.add_argument('--profile', help='Spring Boot Profile (dev/test/prod)')
    parser.add_argument('--host', help='数据库主机')
    parser.add_argument('--port', type=int, default=3306, help='数据库端口 (默认: 3306)')
    parser.add_argument('--database', help='数据库名')
    parser.add_argument('--user', help='用户名')
    parser.add_argument('--password', help='密码')
    parser.add_argument('-o', '--output', help='报告输出路径')
    
    args = parser.parse_args()
    
    # 检查依赖
    missing_deps = []
    if not YAML_AVAILABLE:
        missing_deps.append("pyyaml")
    if not PYMYSQL_AVAILABLE:
        missing_deps.append("pymysql")
    
    if missing_deps:
        print(f"⚠️  缺少依赖: {', '.join(missing_deps)}")
        print(f"💡 请执行: pip install {' '.join(missing_deps)}")
        sys.exit(1)
    
    # 获取数据库连接参数
    if args.project:
        project_root = Path(args.project)
        config_path = ConfigParser.find_config_file(project_root, args.profile)
        
        if not config_path:
            print(f"❌ 未找到配置文件: {project_root}")
            sys.exit(1)
        
        print(f"📝 读取配置: {config_path}")
        
        if config_path.suffix in ['.yml', '.yaml']:
            config = ConfigParser.parse_yaml_config(config_path)
        else:
            config = ConfigParser.parse_properties_config(config_path)
        
        host, port, database, username, password = ConfigParser.extract_db_config(config)
        
        print(f"🔗 连接信息: {host}:{port}/{database} (用户: {username})")
    else:
        # 使用手动指定的参数
        host = args.host or 'localhost'
        port = args.port
        database = args.database
        username = args.user
        password = args.password
        
        if not all([database, username]):
            print("❌ 错误: 需要指定 --project 或手动提供连接参数")
            parser.print_help()
            sys.exit(1)
    
    # 连接并检查
    inspector = DatabaseInspector(host, port, database, username, password)
    
    if not inspector.connect():
        sys.exit(1)
    
    try:
        print(f"✅ 数据库连接成功")
        
        output_path = Path(args.output) if args.output else None
        report = inspector.generate_report(output_path)
        
        if not output_path:
            print(report)
    finally:
        inspector.close()


if __name__ == '__main__':
    main()
