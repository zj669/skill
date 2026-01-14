"""
Novel-Generate 数据库连接池管理
提供 MySQL, Redis, Neo4j, Milvus 的连接管理
"""

from contextlib import contextmanager
from typing import Generator, Optional
import logging

import pymysql
from pymysql.cursors import DictCursor
import redis
from neo4j import GraphDatabase
from pymilvus import connections, utility

from env_config import get_settings

logger = logging.getLogger(__name__)


# ============================================================
# MySQL 连接管理
# ============================================================

class MySQLConnector:
    """MySQL 连接管理器"""
    
    def __init__(self):
        self.config = get_settings().mysql
        self._pool = None
    
    def get_connection(self) -> pymysql.Connection:
        """获取数据库连接"""
        return pymysql.connect(
            host=self.config.host,
            port=self.config.port,
            user=self.config.user,
            password=self.config.password,
            database=self.config.database,
            charset=self.config.charset,
            cursorclass=DictCursor,
            autocommit=True
        )
    
    @contextmanager
    def cursor(self) -> Generator[DictCursor, None, None]:
        """上下文管理器，自动管理连接"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"MySQL error: {e}")
            raise
        finally:
            conn.close()
    
    def execute(self, sql: str, params: tuple = None) -> int:
        """执行 SQL，返回影响行数"""
        with self.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.rowcount
    
    def fetch_one(self, sql: str, params: tuple = None) -> Optional[dict]:
        """查询单条记录"""
        with self.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()
    
    def fetch_all(self, sql: str, params: tuple = None) -> list[dict]:
        """查询多条记录"""
        with self.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()


# ============================================================
# Redis 连接管理
# ============================================================

class RedisConnector:
    """Redis 连接管理器"""
    
    def __init__(self):
        self.config = get_settings().redis
        self._client: Optional[redis.Redis] = None
    
    @property
    def client(self) -> redis.Redis:
        """获取 Redis 客户端 (懒加载)"""
        if self._client is None:
            self._client = redis.Redis(
                host=self.config.host,
                port=self.config.port,
                password=self.config.password,
                db=self.config.db,
                decode_responses=True  # 自动解码为字符串
            )
        return self._client
    
    def ping(self) -> bool:
        """测试连接"""
        try:
            return self.client.ping()
        except redis.ConnectionError:
            return False
    
    def close(self):
        """关闭连接"""
        if self._client:
            self._client.close()
            self._client = None


# ============================================================
# Neo4j 连接管理
# ============================================================

class Neo4jConnector:
    """Neo4j 图数据库连接管理器"""
    
    def __init__(self):
        self.config = get_settings().neo4j
        self._driver = None
    
    @property
    def driver(self):
        """获取 Neo4j Driver (懒加载)"""
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.user, self.config.password)
            )
        return self._driver
    
    @contextmanager
    def session(self):
        """获取会话上下文"""
        session = self.driver.session()
        try:
            yield session
        finally:
            session.close()
    
    def run_query(self, query: str, parameters: dict = None) -> list:
        """执行 Cypher 查询"""
        with self.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]
    
    def ping(self) -> bool:
        """测试连接"""
        try:
            with self.session() as session:
                session.run("RETURN 1")
            return True
        except Exception:
            return False
    
    def close(self):
        """关闭连接"""
        if self._driver:
            self._driver.close()
            self._driver = None


# ============================================================
# Milvus 连接管理
# ============================================================

class MilvusConnector:
    """Milvus 向量数据库连接管理器"""
    
    def __init__(self):
        self.config = get_settings().milvus
        self._connected = False
    
    def connect(self, alias: str = "default"):
        """建立连接"""
        if not self._connected:
            connections.connect(
                alias=alias,
                host=self.config.host,
                port=self.config.port
            )
            self._connected = True
    
    def disconnect(self, alias: str = "default"):
        """断开连接"""
        if self._connected:
            connections.disconnect(alias)
            self._connected = False
    
    def ping(self) -> bool:
        """测试连接"""
        try:
            self.connect()
            utility.list_collections()
            return True
        except Exception:
            return False
    
    def list_collections(self) -> list[str]:
        """列出所有 Collection"""
        self.connect()
        return utility.list_collections()


# ============================================================
# 全局单例
# ============================================================

_mysql_connector: Optional[MySQLConnector] = None
_redis_connector: Optional[RedisConnector] = None
_neo4j_connector: Optional[Neo4jConnector] = None
_milvus_connector: Optional[MilvusConnector] = None


def get_mysql() -> MySQLConnector:
    global _mysql_connector
    if _mysql_connector is None:
        _mysql_connector = MySQLConnector()
    return _mysql_connector


def get_redis() -> RedisConnector:
    global _redis_connector
    if _redis_connector is None:
        _redis_connector = RedisConnector()
    return _redis_connector


def get_neo4j() -> Neo4jConnector:
    global _neo4j_connector
    if _neo4j_connector is None:
        _neo4j_connector = Neo4jConnector()
    return _neo4j_connector


def get_milvus() -> MilvusConnector:
    global _milvus_connector
    if _milvus_connector is None:
        _milvus_connector = MilvusConnector()
    return _milvus_connector


def test_all_connections() -> dict[str, bool]:
    """测试所有数据库连接"""
    results = {}
    
    try:
        mysql = get_mysql()
        mysql.fetch_one("SELECT 1")
        results["mysql"] = True
    except Exception as e:
        logger.error(f"MySQL connection failed: {e}")
        results["mysql"] = False
    
    try:
        results["redis"] = get_redis().ping()
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        results["redis"] = False
    
    try:
        results["neo4j"] = get_neo4j().ping()
    except Exception as e:
        logger.error(f"Neo4j connection failed: {e}")
        results["neo4j"] = False
    
    try:
        results["milvus"] = get_milvus().ping()
    except Exception as e:
        logger.error(f"Milvus connection failed: {e}")
        results["milvus"] = False
    
    return results


if __name__ == "__main__":
    """测试所有连接"""
    print("=== 测试数据库连接 ===\n")
    
    results = test_all_connections()
    
    for name, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {name}: {'Connected' if status else 'Failed'}")
