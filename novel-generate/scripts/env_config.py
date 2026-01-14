"""
Novel-Generate 环境配置管理
使用 pydantic-settings 从环境变量和 .env 文件加载配置
"""

import os
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class MySQLSettings(BaseSettings):
    """MySQL 数据库配置"""
    host: str = Field(default="localhost", alias="MYSQL_HOST")
    port: int = Field(default=3306, alias="MYSQL_PORT")
    user: str = Field(default="novel", alias="MYSQL_USER")
    password: str = Field(default="novel123", alias="MYSQL_PASSWORD")
    database: str = Field(default="novel_db", alias="MYSQL_DATABASE")
    charset: str = Field(default="utf8mb4", alias="MYSQL_CHARSET")
    
    @property
    def connection_string(self) -> str:
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?charset={self.charset}"

    class Config:
        env_prefix = ""
        extra = "ignore"


class RedisSettings(BaseSettings):
    """Redis 配置"""
    host: str = Field(default="localhost", alias="REDIS_HOST")
    port: int = Field(default=6379, alias="REDIS_PORT")
    password: str | None = Field(default=None, alias="REDIS_PASSWORD")
    db: int = Field(default=0, alias="REDIS_DB")
    
    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"

    class Config:
        env_prefix = ""
        extra = "ignore"


class Neo4jSettings(BaseSettings):
    """Neo4j 图数据库配置"""
    uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    user: str = Field(default="neo4j", alias="NEO4J_USER")
    password: str = Field(default="novel123", alias="NEO4J_PASSWORD")

    class Config:
        env_prefix = ""
        extra = "ignore"


class MilvusSettings(BaseSettings):
    """Milvus 向量数据库配置"""
    host: str = Field(default="localhost", alias="MILVUS_HOST")
    port: str = Field(default="19530", alias="MILVUS_PORT")
    
    # Collection 名称
    world_collection: str = "world_knowledge"
    chapter_collection: str = "chapter_memories"
    voice_collection: str = "character_voices"
    
    # 向量维度
    vector_dim: int = 1024

    class Config:
        env_prefix = ""
        extra = "ignore"


class EmbeddingSettings(BaseSettings):
    """向量嵌入模型配置"""
    # 支持多种嵌入方式
    provider: str = Field(default="openai", alias="EMBEDDING_PROVIDER")
    
    # Sentence Transformers 模型
    model_name: str = Field(default="BAAI/bge-large-zh-v1.5", alias="EMBEDDING_MODEL")
    
    # OpenAI API (可选)
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: str | None = Field(default=None, alias="OPENAI_BASE_URL")
    openai_model: str = Field(default="text-embedding-3-small", alias="OPENAI_EMBEDDING_MODEL")

    class Config:
        env_prefix = ""
        extra = "ignore"


class AppSettings(BaseSettings):
    """应用级配置"""
    # 数据目录
    data_dir: Path = Field(default=Path("./data"), alias="DATA_DIR")
    char_cards_dir: Path = Field(default=Path("./data/char_cards"), alias="CHAR_CARDS_DIR")
    drafts_dir: Path = Field(default=Path("./data/drafts"), alias="DRAFTS_DIR")
    logs_dir: Path = Field(default=Path("./data/logs"), alias="LOGS_DIR")
    
    # 默认小说 ID
    default_novel_id: str = Field(default="novel_001", alias="DEFAULT_NOVEL_ID")
    
    # 调试模式
    debug: bool = Field(default=False, alias="DEBUG")

    class Config:
        env_prefix = ""
        extra = "ignore"

    def ensure_dirs(self):
        """确保所有数据目录存在"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.char_cards_dir.mkdir(parents=True, exist_ok=True)
        self.drafts_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    """主配置类，聚合所有子配置"""
    mysql: MySQLSettings = MySQLSettings()
    redis: RedisSettings = RedisSettings()
    neo4j: Neo4jSettings = Neo4jSettings()
    milvus: MilvusSettings = MilvusSettings()
    embedding: EmbeddingSettings = EmbeddingSettings()
    app: AppSettings = AppSettings()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """
    获取配置单例
    优先级: 环境变量 > .env 文件 > 默认值
    """
    from dotenv import load_dotenv
    
    # 必须在创建 Settings 实例之前加载 .env
    # 因为 pydantic-settings 在实例化时读取环境变量
    env_paths = [
        Path(".env"),
        Path(__file__).parent / ".env",  # scripts/.env
        Path("../docker/.env"),
        Path(__file__).parent.parent / "docker" / ".env",
    ]
    
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path, override=True)
            break
    
    # 现在创建 Settings，子配置会自动从环境变量读取
    settings = Settings(
        mysql=MySQLSettings(),
        redis=RedisSettings(),
        neo4j=Neo4jSettings(),
        milvus=MilvusSettings(),
        embedding=EmbeddingSettings(),
        app=AppSettings()
    )
    settings.app.ensure_dirs()
    return settings


# 便捷访问
settings = get_settings()


if __name__ == "__main__":
    """测试配置加载"""
    print("=== Novel-Generate 配置 ===\n")
    
    s = get_settings()
    
    print(f"MySQL: {s.mysql.host}:{s.mysql.port}/{s.mysql.database}")
    print(f"Redis: {s.redis.host}:{s.redis.port}")
    print(f"Neo4j: {s.neo4j.uri}")
    print(f"Milvus: {s.milvus.host}:{s.milvus.port}")
    print(f"Embedding: {s.embedding.provider} / {s.embedding.model_name}")
    print(f"\nData Dir: {s.app.data_dir}")
    print(f"Debug: {s.app.debug}")
