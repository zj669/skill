# Novel-Generate 中间件启动指南

## 快速启动

```bash
# 进入 docker 目录
cd docker

# 启动所有服务 (后台运行)
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

## 服务端口

| 服务 | 端口 | 用途 |
|------|------|------|
| MySQL | 3306 | 章节进度/事件日志 |
| Redis | 6379 | 爽点曲线/悬念队列 |
| Neo4j HTTP | 7474 | 浏览器管理界面 |
| Neo4j Bolt | 7687 | 程序连接 |
| Milvus | 19530 | 向量检索 |
| MinIO Console | 9001 | 对象存储管理 |

## 验证连接

### MySQL
```bash
docker exec -it novel-mysql mysql -u novel -pnovel123 novel_db -e "SHOW TABLES;"
```

### Redis
```bash
docker exec -it novel-redis redis-cli ping
```

### Neo4j
浏览器访问: http://localhost:7474
用户名: neo4j
密码: novel123

### Milvus
```python
from pymilvus import connections
connections.connect("default", host="localhost", port="19530")
print("Milvus connected!")
```

## 初始化 Milvus Collections

```bash
# 安装依赖
pip install pymilvus

# 运行初始化脚本
python init/milvus/init_collections.py
```

## 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷 (清空数据)
docker-compose down -v
```

## 数据持久化

所有数据通过 Docker Volumes 持久化：
- `mysql_data`: MySQL 数据
- `redis_data`: Redis 数据
- `neo4j_data`: Neo4j 数据
- `milvus_data`: Milvus 数据
- `minio_data`: MinIO 对象存储
- `etcd_data`: Milvus 元数据
