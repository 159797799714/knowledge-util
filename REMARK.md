# 掌柜智库 (knowledge-base) 项目说明

## 一、项目概述

掌柜智库是一个基于 **RAG（Retrieval-Augmented Generation）** 技术的企业知识库问答系统，主要用于处理和查询商品相关文档。系统采用 **LangGraph** 构建业务流程，实现文档导入和智能查询两大核心功能。

---

## 二、技术架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                          前端页面                                    │
│  ┌──────────────────┐    ┌──────────────────┐                       │
│  │   import.html    │    │    chat.html     │                       │
│  │  (文档上传页面)   │    │   (对话查询页面)  │                       │
│  └────────┬─────────┘    └────────┬─────────┘                       │
└───────────┼────────────────────────┼─────────────────────────────────┘
            │                        │
            ▼                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FastAPI 服务层                              │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    import_service (端口 8000)                  │  │
│  │  /upload → /status/{task_id} → /import.html                   │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    query_service (端口 8001)                   │  │
│  │  /query → /stream/{session_id} → /chat.html → /health         │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       LangGraph 工作流层                            │
│  ┌─────────────────────┐    ┌───────────────────────────────────┐  │
│  │   KBImportWorkflow  │    │         KBQueryWorkflow           │  │
│  │  (文档导入流程)       │    │      (智能查询流程)               │  │
│  └─────────────────────┘    └───────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        外部服务依赖                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │
│  │   Milvus    │  │  MongoDB    │  │   MinIO     │  │   LLM API │  │
│  │  (向量库)   │  │  (文档库)   │  │  (对象存储)  │  │ (DashScope)││
│  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈

| 类别 | 技术 | 版本要求 |
|------|------|----------|
| 语言 | Python | >= 3.11 |
| 包管理 | uv | - |
| Web 框架 | FastAPI | >= 0.136.1 |
| 流程编排 | LangGraph | >= 1.1.10 |
| 向量数据库 | Milvus | >= 3.0.0 |
| 文档数据库 | MongoDB | >= 4.17.0 |
| 对象存储 | MinIO | >= 7.2.20 |
| 嵌入模型 | BGE-M3 | - |
| 重排模型 | BGE Reranker | - |
| LLM | Qwen (DashScope) | - |
| 运行时 | PyTorch | >= 2.11.0 (CUDA) |

---

## 三、核心流程

### 3.1 文档导入流程 (KBImportWorkflow)

```
node_entry → [条件路由] → node_pdf_to_md → node_md_img → node_document_split
    → node_item_name_recognition → node_bge_embedding → node_import_milvus → END
```

| 节点 | 功能说明 |
|------|----------|
| node_entry | 入口节点，判断文档类型（PDF/MD） |
| node_pdf_to_md | 将 PDF 文件转换为 Markdown 格式 |
| node_md_img | 解析文档中的图片，提取图片含义并嵌入文档 |
| node_document_split | 将文档切分为小块（Chunk） |
| node_item_name_recognition | 识别文档中的商品名称 |
| node_bge_embedding | 使用 BGE-M3 模型将文本转换为向量 |
| node_import_milvus | 将向量和标量数据存入 Milvus |

### 3.2 智能查询流程 (KBQueryWorkflow)

```
node_item_name_confirm → [条件路由]
    ├─→ (已有答案) → node_answer_output → END
    └─→ (需要搜索) → node_multi_search → [并发搜索]
        ├─→ node_search_embedding (向量搜索)
        ├─→ node_search_embedding_hyde (HyDE 搜索)
        └─→ node_web_search_mcp (联网搜索)
    → node_join (结果合并) → node_rrf (排序) → node_rerank (重排)
    → node_answer_output (答案生成) → END
```

| 节点 | 功能说明 |
|------|----------|
| node_item_name_confirm | 确认查询中的商品名称，支持反问/拒绝场景 |
| node_search_embedding | 在 Milvus 中进行向量相似度搜索 |
| node_search_embedding_hyde | 使用 HyDE（Hypothetical Document Embeddings）搜索 |
| node_web_search_mcp | 通过 MCP 服务进行联网搜索 |
| node_rrf | 使用 RRF（Reciprocal Rank Fusion）算法合并多路搜索结果 |
| node_rerank | 使用 BGE Reranker 对结果进行重排序 |
| node_answer_output | 调用 LLM 生成最终回答 |

---

## 四、外部服务依赖

### 4.1 必需服务

| 服务 | 默认地址 | 用途 |
|------|----------|------|
| Milvus | `http://localhost:19530` | 向量数据库，存储文档嵌入向量 |
| MongoDB | `mongodb://localhost:27017` | 文档数据库，存储会话历史记录 |
| MinIO | `localhost:9000` | 对象存储，存储上传的文档文件 |
| LLM API | `https://dashscope.aliyuncs.com` | 阿里云 DashScope API，提供 LLM 能力 |

### 4.2 启动外部服务（推荐使用 Docker）

```bash
# Milvus
docker run -d --name milvus -p 19530:19530 milvusdb/milvus:v3.0.0

# MongoDB
docker run -d --name mongodb -p 27017:27017 mongo:6.0

# MinIO
docker run -d --name minio -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address ":9001"
```

---

## 五、环境配置

### 5.1 创建环境变量文件

复制 `.env.example` 为 `.env`，并根据实际情况修改配置：

```bash
cp .env.example .env
```

### 5.2 关键配置项说明

| 配置项 | 说明 | 示例值 |
|--------|------|--------|
| OPENAI_API_KEY | DashScope API 密钥 | `sk-xxxxxxxxxx` |
| OPENAI_API_BASE | API 基础地址 | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| BGE_M3_PATH | BGE-M3 模型本地路径 | `D:/ai_models/modelscope_cache/models/BAAI/bge-m3` |
| BGE_DEVICE | 嵌入模型运行设备 | `cuda:0` 或 `cpu` |
| MILVUS_URL | Milvus 连接地址 | `http://localhost:19530` |
| MONGO_URL | MongoDB 连接地址 | `mongodb://localhost:27017` |
| MINIO_ENDPOINT | MinIO 服务端点 | `localhost:9000` |
| MODELSCOPE_CACHE | ModelScope 模型缓存路径 | `D:/ai_models/modelscope_cache` |
| DATA_BASED_ROOT_DIR | 数据存储根目录（上传文件保存路径） | `./doc/` |

---

## 六、启动步骤

### 6.1 安装依赖

```bash
# 使用 uv 安装依赖（推荐）
uv sync

# 或使用 pip（需要先创建虚拟环境）
python -m venv venv
.\venv\Scripts\activate
pip install -e .
```

### 6.2 下载模型（首次启动前）

```bash
# 下载 BGE-M3 嵌入模型
python tool/download_bgem3.py

# 下载 BGE Reranker 重排模型
python tool/download_bge_reranker_large.py
```

### 6.3 启动服务

**方式一：使用 Python 直接启动（推荐用于开发）**

```bash
# 启动导入服务（端口 8000）
python web/api/import_service.py

# 启动查询服务（端口 8001）
python web/api/query_service.py
```

**方式二：使用 uvicorn 启动**

```bash
# 启动导入服务
uvicorn web.api.import_service:app --host 127.0.0.1 --port 8000

# 启动查询服务
uvicorn web.api.query_service:app --host 127.0.0.1 --port 8001
```

### 6.4 验证服务

```bash
# 检查导入服务健康状态
curl http://localhost:8000/status/test

# 检查查询服务健康状态
curl http://localhost:8001/health
```

---

## 七、访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 导入页面 | `http://localhost:8000/import.html` | 文档上传前端页面 |
| 导入 API 文档 | `http://localhost:8000/docs` | Swagger UI 接口文档 |
| 查询页面 | `http://localhost:8001/chat.html` | 对话查询前端页面 |
| 查询 API 文档 | `http://localhost:8001/docs` | Swagger UI 接口文档 |

---

## 八、目录结构

```
knowledge_base/
├── config/           # 配置文件（嵌入、LLM、Milvus、MinIO等）
├── processor/        # LangGraph 处理器
│   ├── import_processor/    # 导入流程（节点、状态、主图）
│   └── query_processor/     # 查询流程（节点、状态、主图）
├── tool/             # 工具脚本（模型下载、日志配置）
├── utils/            # 工具函数（向量、Milvus、MinIO、SSE等）
├── web/              # Web 服务层
│   ├── api/          # API 接口（import_service、query_service）
│   └── page/         # 前端页面（import.html、chat.html）
├── test/             # 测试代码（FastAPI、SSE、导入/查询测试）
├── .env              # 环境变量
├── .env.example      # 环境变量示例
├── pyproject.toml    # 项目配置
└── uv.lock           # 依赖锁文件
```

---

## 九、注意事项

1. **CUDA 环境**：建议使用 GPU 运行嵌入模型和重排模型，需安装 CUDA 12.8+
2. **模型下载**：首次启动前需下载 BGE-M3 和 BGE Reranker 模型
3. **端口占用**：确保端口 8000、8001、19530、27017、9000 未被占用
4. **数据目录**：确保 `DATA_BASED_ROOT_DIR` 环境变量指向的目录存在且有写入权限
5. **日志**：系统使用 colorlog 输出日志，可在 `tool/logger.py` 中调整日志级别
6. **环境变量**：`import_service.py` 中使用了 `DATA_BASED_ROOT_DIR` 环境变量，需在 `.env` 文件中配置，否则会导致文件上传失败
7. **配置文件**：复制 `.env.example` 时需注意，原始文件中曾有多余字符（已修复）