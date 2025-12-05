# GraphRAG Docker 部署指南

本文档介绍如何使用 Docker 运行 GraphRAG 智能图RAG旅游助手。

## 📋 前置要求

- [Docker](https://docs.docker.com/get-docker/) >= 20.10
- [Docker Compose](https://docs.docker.com/compose/install/) >= 2.0
- 至少 8GB 可用内存
- 至少 20GB 磁盘空间

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/your-username/rag_graph.git
cd rag_graph
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的 API 密钥
nano .env  # 或使用你喜欢的编辑器
```

**必须配置的变量：**
- `LLM_API_KEY`: 你的 LLM API 密钥 (如 DeepSeek, OpenAI 等)
- `NEO4J_PASSWORD`: Neo4j 数据库密码 (建议修改默认值)

### 3. 启动服务

```bash
# 构建并启动所有服务 (首次运行需要较长时间)
docker-compose up -d --build

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f graphrag-app
```

### 4. 使用 GraphRAG

#### 交互式模式 (推荐)

```bash
# 进入交互式界面
docker-compose exec graphrag-app python main.py start
```

#### 单次查询模式

```bash
docker-compose exec graphrag-app python main.py query "北京有什么好玩的地方？"
```

#### 系统健康检查

```bash
docker-compose exec graphrag-app python main.py doctor
```

## 🔧 服务说明

| 服务 | 端口 | 说明 |
|------|------|------|
| graphrag-app | - | GraphRAG 主应用 |
| milvus-standalone | 19530, 9091 | Milvus 向量数据库 |
| neo4j | 7474 (HTTP), 7687 (Bolt) | Neo4j 图数据库 |
| minio | 9000, 9001 | MinIO 对象存储 (Milvus 依赖) |
| etcd | - | etcd 键值存储 (Milvus 依赖) |

## 🌐 访问 Web 界面

- **Neo4j Browser**: http://localhost:7474
  - 用户名: `neo4j`
  - 密码: 你在 `.env` 中设置的 `NEO4J_PASSWORD`
  
- **MinIO Console**: http://localhost:9001
  - 用户名: `minioadmin`
  - 密码: `minioadmin`

## 📁 数据持久化

所有数据存储在 `./volumes/` 目录下：

```
volumes/
├── etcd/          # etcd 数据
├── milvus/        # Milvus 向量索引
├── minio/         # MinIO 对象存储
└── neo4j/         # Neo4j 图数据
    ├── data/
    ├── logs/
    └── import/
```

## 🔄 常用命令

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重新构建应用镜像
docker-compose build graphrag-app

# 查看应用日志
docker-compose logs -f graphrag-app

# 进入应用容器
docker-compose exec graphrag-app bash

# 清理所有数据 (谨慎使用!)
docker-compose down -v
rm -rf volumes/
```

## 🐳 单独使用 Docker 镜像

如果你只想使用 GraphRAG 应用，而数据库服务已经在其他地方运行：

```bash
# 构建镜像
docker build -t graphrag:latest .

# 运行容器
docker run -it --rm \
  -e NEO4J_URI=neo4j://your-neo4j-host:7687 \
  -e NEO4J_USER=neo4j \
  -e NEO4J_PASSWORD=your_password \
  -e MILVUS_HOST=your-milvus-host \
  -e MILVUS_PORT=19530 \
  -e LLM_API_KEY=your_api_key \
  -e LLM_BASE_URL=https://api.deepseek.com/v1 \
  graphrag:latest start
```

## 🔧 故障排除

### 1. 服务启动失败

```bash
# 检查服务状态
docker-compose ps

# 查看详细日志
docker-compose logs [service-name]
```

### 2. Milvus 连接失败

Milvus 启动较慢，请等待健康检查通过：

```bash
# 检查 Milvus 健康状态
curl http://localhost:9091/healthz
```

### 3. 模型下载缓慢

首次运行时需要下载 Embedding 模型，如果网络较慢，可以：

1. 使用镜像站点（设置 `HF_ENDPOINT` 环境变量）
2. 预先下载模型到 `volumes/` 目录

### 4. 内存不足

如果出现 OOM 错误，请增加 Docker 的内存限制（建议至少 8GB）。

## 📄 发布到 Docker Hub

如果你想将镜像发布到 Docker Hub 供其他人使用：

```bash
# 登录 Docker Hub
docker login

# 构建并标记镜像
docker build -t your-username/graphrag:latest .

# 推送到 Docker Hub
docker push your-username/graphrag:latest
```

其他用户可以直接拉取使用：

```bash
docker pull your-username/graphrag:latest
```

## 📝 许可证

MIT License
