"""
Novel-Generate RAG 引擎
负责 Milvus 向量检索和嵌入操作

功能：
- 知识库初始化 (从 MD 文件)
- 向量检索
- 内容入库
- 嵌入生成
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, List
import logging

import numpy as np
from pymilvus import (
    Collection,
    utility,
    connections
)

from env_config import get_settings
from db_connector import get_milvus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


# ============================================================
# 嵌入模型管理
# ============================================================

class EmbeddingModel:
    """嵌入模型封装"""
    
    def __init__(self):
        self.config = settings.embedding
        self._model = None
    
    def _load_model(self):
        """懒加载模型"""
        if self._model is None:
            if self.config.provider == "sentence-transformers":
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading model: {self.config.model_name}")
                self._model = SentenceTransformer(self.config.model_name)
            elif self.config.provider == "openai":
                from openai import OpenAI
                self._model = OpenAI(
                    api_key=self.config.openai_api_key,
                    base_url=self.config.openai_base_url
                )
            else:
                raise ValueError(f"Unknown embedding provider: {self.config.provider}")
    
    def embed(self, texts: List[str]) -> np.ndarray:
        """生成文本嵌入向量"""
        self._load_model()
        
        if self.config.provider == "sentence-transformers":
            embeddings = self._model.encode(texts, normalize_embeddings=True)
            return embeddings
        elif self.config.provider == "openai":
            # 确保 texts 不为空
            if not texts:
                return np.array([])
            
            # 替换换行符，某些 API 对换行符敏感
            texts = [t.replace("\n", " ") for t in texts]
            
            try:
                response = self._model.embeddings.create(
                    model=self.config.openai_model,
                    input=texts
                )
                return np.array([d.embedding for d in response.data])
            except Exception as e:
                logger.error(f"OpenAI Embedding error: {e}")
                raise
        
        return np.array([])
    
    def embed_single(self, text: str) -> np.ndarray:
        """生成单个文本的嵌入向量"""
        return self.embed([text])[0]


# 全局嵌入模型实例
_embedding_model: Optional[EmbeddingModel] = None


def get_embedding_model() -> EmbeddingModel:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel()
    return _embedding_model


# ============================================================
# 文本切片
# ============================================================

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """将长文本切分为较小的块"""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # 尝试在句号或换行处断开
        if end < len(text):
            last_break = max(
                chunk.rfind('。'),
                chunk.rfind('\n'),
                chunk.rfind('！'),
                chunk.rfind('？')
            )
            if last_break > chunk_size // 2:
                chunk = text[start:start + last_break + 1]
                end = start + last_break + 1
        
        chunks.append(chunk.strip())
        start = end - overlap
    
    return [c for c in chunks if c]


# ============================================================
# 知识库操作
# ============================================================

def init_knowledge_base(source_dir: str, novel_id: str = None) -> dict:
    """
    初始化知识库
    读取 source_dir 下的所有 MD 文件，切片并存入 Milvus
    """
    novel_id = novel_id or settings.app.default_novel_id
    source_path = Path(source_dir)
    
    if not source_path.exists():
        return {
            "status": "FAILED",
            "error_code": "E101",
            "message": f"Source directory not found: {source_dir}"
        }
    
    # 连接 Milvus
    milvus = get_milvus()
    milvus.connect()
    
    collection_name = settings.milvus.world_collection
    
    if not utility.has_collection(collection_name):
        return {
            "status": "FAILED",
            "error_code": "E102",
            "message": f"Collection not found: {collection_name}. Run init_collections.py first."
        }
    
    collection = Collection(collection_name)
    collection.load()
    
    # 获取嵌入模型
    embed_model = get_embedding_model()
    
    # 文档类型映射
    doc_type_map = {
        "levels": "level",
        "geography": "geography",
        "items": "item",
        "techniques": "technique",
        "factions": "faction",
    }
    
    md_files = list(source_path.glob("*.md"))
    total_chunks = 0
    
    for md_file in md_files:
        logger.info(f"Processing: {md_file.name}")
        
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 确定文档类型
        doc_type = "general"
        for key, dtype in doc_type_map.items():
            if key in md_file.stem.lower():
                doc_type = dtype
                break
        
        # 切片
        chunks = chunk_text(content)
        
        if not chunks:
            continue
        
        # 生成嵌入
        vectors = embed_model.embed(chunks)
        
        # 准备数据
        entities = [
            [novel_id] * len(chunks),  # novel_id
            chunks,                      # text
            [md_file.name] * len(chunks),  # source
            [doc_type] * len(chunks),    # doc_type
            vectors.tolist()             # vector
        ]
        
        # 插入
        collection.insert(entities)
        total_chunks += len(chunks)
        logger.info(f"  Inserted {len(chunks)} chunks from {md_file.name}")
    
    # 刷新索引
    collection.flush()
    
    return {
        "status": "SUCCESS",
        "data": {
            "files_processed": len(md_files),
            "total_chunks": total_chunks
        }
    }


def query_rag(query: str, novel_id: str = None, top_k: int = 3, 
              doc_type: str = None) -> dict:
    """
    查询 RAG 知识库
    返回最相关的 top_k 个文本片段
    """
    novel_id = novel_id or settings.app.default_novel_id
    
    # 连接 Milvus
    milvus = get_milvus()
    milvus.connect()
    
    collection_name = settings.milvus.world_collection
    
    if not utility.has_collection(collection_name):
        return {
            "status": "FAILED",
            "error_code": "E102",
            "message": f"Collection not found: {collection_name}"
        }
    
    collection = Collection(collection_name)
    collection.load()
    
    # 生成查询向量
    embed_model = get_embedding_model()
    query_vector = embed_model.embed_single(query)
    
    # 构建过滤条件
    expr = f'novel_id == "{novel_id}"'
    if doc_type:
        expr += f' and doc_type == "{doc_type}"'
    
    # 搜索
    search_params = {
        "metric_type": "COSINE",
        "params": {"nprobe": 10}
    }
    
    results = collection.search(
        data=[query_vector.tolist()],
        anns_field="vector",
        param=search_params,
        limit=top_k,
        expr=expr,
        output_fields=["text", "source", "doc_type"]
    )
    
    # 格式化结果
    hits = []
    for hit in results[0]:
        hits.append({
            "text": hit.entity.get("text"),
            "source": hit.entity.get("source"),
            "doc_type": hit.entity.get("doc_type"),
            "score": hit.distance
        })
    
    return {
        "status": "SUCCESS",
        "data": {
            "query": query,
            "results": hits
        }
    }


def ingest_text(text: str, text_type: str, novel_id: str = None,
                chapter_num: int = None) -> dict:
    """
    将新文本入库
    """
    novel_id = novel_id or settings.app.default_novel_id
    
    # 连接 Milvus
    milvus = get_milvus()
    milvus.connect()
    
    # 根据类型选择 Collection
    if text_type in ["chapter_summary", "memory"]:
        collection_name = settings.milvus.chapter_collection
    else:
        collection_name = settings.milvus.world_collection
    
    if not utility.has_collection(collection_name):
        return {
            "status": "FAILED",
            "error_code": "E102",
            "message": f"Collection not found: {collection_name}"
        }
    
    collection = Collection(collection_name)
    
    # 生成嵌入
    embed_model = get_embedding_model()
    vector = embed_model.embed_single(text)
    
    # 根据 Collection 类型准备数据
    if collection_name == settings.milvus.chapter_collection:
        entities = [
            [novel_id],
            [chapter_num or 0],
            [text],
            [""],  # key_events placeholder
            [vector.tolist()]
        ]
    else:
        entities = [
            [novel_id],
            [text],
            ["runtime"],
            [text_type],
            [vector.tolist()]
        ]
    
    collection.insert(entities)
    collection.flush()
    
    return {
        "status": "SUCCESS",
        "message": f"Text ingested as type: {text_type}"
    }


def search_chapter_memory(query: str, novel_id: str = None, 
                          top_k: int = 5) -> dict:
    """
    搜索章节记忆
    """
    novel_id = novel_id or settings.app.default_novel_id
    
    milvus = get_milvus()
    milvus.connect()
    
    collection_name = settings.milvus.chapter_collection
    
    if not utility.has_collection(collection_name):
        return {
            "status": "FAILED",
            "error_code": "E102",
            "message": f"Collection not found: {collection_name}"
        }
    
    collection = Collection(collection_name)
    collection.load()
    
    embed_model = get_embedding_model()
    query_vector = embed_model.embed_single(query)
    
    search_params = {
        "metric_type": "COSINE",
        "params": {"nprobe": 10}
    }
    
    results = collection.search(
        data=[query_vector.tolist()],
        anns_field="vector",
        param=search_params,
        limit=top_k,
        expr=f'novel_id == "{novel_id}"',
        output_fields=["chapter_num", "summary"]
    )
    
    hits = []
    for hit in results[0]:
        hits.append({
            "chapter": hit.entity.get("chapter_num"),
            "summary": hit.entity.get("summary"),
            "score": hit.distance
        })
    
    return {
        "status": "SUCCESS",
        "data": {
            "query": query,
            "results": hits
        }
    }


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Novel-Generate RAG Engine")
    parser.add_argument("--action", help="Action: init, ingest, search_memory")
    parser.add_argument("--source_dir", help="Source directory for init")
    parser.add_argument("--query", help="Query string for search")
    parser.add_argument("--top_k", type=int, default=3, help="Number of results")
    parser.add_argument("--text", help="Text to ingest")
    parser.add_argument("--type", help="Text type for ingest")
    parser.add_argument("--novel_id", help="Novel ID")
    parser.add_argument("--doc_type", help="Filter by document type")
    parser.add_argument("--chapter", type=int, help="Chapter number")
    
    args = parser.parse_args()
    novel_id = args.novel_id or settings.app.default_novel_id
    
    # 如果有 query 参数且没有 action，执行搜索
    if args.query and not args.action:
        result = query_rag(args.query, novel_id, args.top_k, args.doc_type)
    elif args.action == "init":
        result = init_knowledge_base(args.source_dir, novel_id)
    elif args.action == "ingest":
        result = ingest_text(args.text, args.type, novel_id, args.chapter)
    elif args.action == "search_memory":
        result = search_chapter_memory(args.query, novel_id, args.top_k)
    else:
        result = {"status": "FAILED", "message": "No valid action specified. Use --query or --action"}
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("status") == "SUCCESS" else 1)


if __name__ == "__main__":
    main()
