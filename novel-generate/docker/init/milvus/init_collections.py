"""
Novel-Generate Milvus Collection 初始化脚本
创建向量库的 Collection Schema

使用前请确保 Milvus 服务已启动。
运行方式: python init_collections.py
"""

from pymilvus import (
    connections,
    utility,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType
)

# ============================================================
# 配置
# ============================================================

MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"

# 向量维度 (使用 1024 维，适配大多数嵌入模型)
VECTOR_DIM = 1024

# ============================================================
# Collection 定义
# ============================================================

def create_world_knowledge_collection():
    """
    世界观知识库
    存储: 境界设定、地图描写、功法特效、物品说明等
    用于: RAG 检索，为正文写作提供素材
    """
    collection_name = "world_knowledge"
    
    if utility.has_collection(collection_name):
        print(f"Collection '{collection_name}' already exists, skipping...")
        return
    
    schema = CollectionSchema(
        fields=[
            FieldSchema(
                name="id",
                dtype=DataType.INT64,
                is_primary=True,
                auto_id=True
            ),
            FieldSchema(
                name="novel_id",
                dtype=DataType.VARCHAR,
                max_length=64,
                description="小说标识"
            ),
            FieldSchema(
                name="text",
                dtype=DataType.VARCHAR,
                max_length=4096,
                description="原始文本内容"
            ),
            FieldSchema(
                name="source",
                dtype=DataType.VARCHAR,
                max_length=256,
                description="来源文件, 如 levels.md"
            ),
            FieldSchema(
                name="doc_type",
                dtype=DataType.VARCHAR,
                max_length=64,
                description="文档类型: level/geography/item/technique/faction"
            ),
            FieldSchema(
                name="vector",
                dtype=DataType.FLOAT_VECTOR,
                dim=VECTOR_DIM,
                description="文本向量"
            )
        ],
        description="世界观知识库 - 用于 RAG 检索设定素材"
    )
    
    collection = Collection(name=collection_name, schema=schema)
    
    # 创建索引
    index_params = {
        "metric_type": "COSINE",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128}
    }
    collection.create_index(field_name="vector", index_params=index_params)
    
    print(f"Created collection: {collection_name}")
    return collection


def create_chapter_memories_collection():
    """
    章节记忆库
    存储: 各章节的摘要向量
    用于: 长期记忆检索，查找相关历史剧情
    """
    collection_name = "chapter_memories"
    
    if utility.has_collection(collection_name):
        print(f"Collection '{collection_name}' already exists, skipping...")
        return
    
    schema = CollectionSchema(
        fields=[
            FieldSchema(
                name="id",
                dtype=DataType.INT64,
                is_primary=True,
                auto_id=True
            ),
            FieldSchema(
                name="novel_id",
                dtype=DataType.VARCHAR,
                max_length=64,
                description="小说标识"
            ),
            FieldSchema(
                name="chapter_num",
                dtype=DataType.INT64,
                description="章节编号"
            ),
            FieldSchema(
                name="summary",
                dtype=DataType.VARCHAR,
                max_length=2048,
                description="章节摘要"
            ),
            FieldSchema(
                name="key_events",
                dtype=DataType.VARCHAR,
                max_length=1024,
                description="关键事件列表 (JSON数组字符串)"
            ),
            FieldSchema(
                name="vector",
                dtype=DataType.FLOAT_VECTOR,
                dim=VECTOR_DIM,
                description="摘要向量"
            )
        ],
        description="章节记忆库 - 用于长期记忆检索"
    )
    
    collection = Collection(name=collection_name, schema=schema)
    
    # 创建索引
    index_params = {
        "metric_type": "COSINE",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128}
    }
    collection.create_index(field_name="vector", index_params=index_params)
    
    print(f"Created collection: {collection_name}")
    return collection


def create_character_voices_collection():
    """
    角色语气库
    存储: 各角色的对话样本
    用于: Few-Shot 注入，保持角色语气一致
    """
    collection_name = "character_voices"
    
    if utility.has_collection(collection_name):
        print(f"Collection '{collection_name}' already exists, skipping...")
        return
    
    schema = CollectionSchema(
        fields=[
            FieldSchema(
                name="id",
                dtype=DataType.INT64,
                is_primary=True,
                auto_id=True
            ),
            FieldSchema(
                name="novel_id",
                dtype=DataType.VARCHAR,
                max_length=64,
                description="小说标识"
            ),
            FieldSchema(
                name="character_name",
                dtype=DataType.VARCHAR,
                max_length=64,
                description="角色名称"
            ),
            FieldSchema(
                name="dialogue",
                dtype=DataType.VARCHAR,
                max_length=512,
                description="对话样本"
            ),
            FieldSchema(
                name="emotion",
                dtype=DataType.VARCHAR,
                max_length=32,
                description="情绪标签: 愤怒/得意/悲伤/平静等"
            ),
            FieldSchema(
                name="vector",
                dtype=DataType.FLOAT_VECTOR,
                dim=VECTOR_DIM,
                description="对话向量"
            )
        ],
        description="角色语气库 - 用于 Few-Shot 注入"
    )
    
    collection = Collection(name=collection_name, schema=schema)
    
    # 创建索引
    index_params = {
        "metric_type": "COSINE",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 64}
    }
    collection.create_index(field_name="vector", index_params=index_params)
    
    print(f"Created collection: {collection_name}")
    return collection


# ============================================================
# 主函数
# ============================================================

def main():
    print(f"Connecting to Milvus at {MILVUS_HOST}:{MILVUS_PORT}...")
    connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
    
    print("\nCreating collections...")
    create_world_knowledge_collection()
    create_chapter_memories_collection()
    create_character_voices_collection()
    
    print("\nAll collections created successfully!")
    print("\nExisting collections:")
    for name in utility.list_collections():
        print(f"  - {name}")
    
    connections.disconnect("default")


if __name__ == "__main__":
    main()
