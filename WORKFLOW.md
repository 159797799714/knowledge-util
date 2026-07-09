# 掌柜智库工作流文档

> 本文档详细描述了掌柜智库两个核心服务的完整运行流程：Import Service（知识库导入服务）和 Query Service（查询会话服务）。

---

## 📦 一、Import Service（知识库导入服务）

### 1.1 文件上传接口 `/upload` 完整流程

```
前端 POST /upload (form-data)
       ↓
┌─────────────────────────────────────────────────────────────┐
│  upload_files(background_tasks, files)                      │
├─────────────────────────────────────────────────────────────┤
│  1. 构建本地存储根目录: DATA_BASED_ROOT_DIR/YYYYMMDD         │
│                                                              │
│  2. 遍历每个上传文件:                                         │
│     ├─ 生成唯一 task_id (UUID4)                              │
│     ├─ add_running_task(task_id, "upload_file")              │
│     ├─ 创建任务目录: DATA_BASED_ROOT_DIR/YYYYMMDD/{task_id}   │
│     ├─ 保存文件到本地: {task_id}/{filename}                  │
│     ├─ 上传到 MinIO: pdf_files/YYYYMMDD/{filename}          │
│     ├─ add_done_task(task_id, "upload_file")                 │
│     └─ background_tasks.add_task(run_graph_task, ...)        │
│                                                              │
│  3. 返回: {"code":200, "message":..., "task_ids":[...]}     │
└─────────────────────────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────────────────────┐
│  run_graph_task(task_id, file_dir, import_file_path)        │
│  [后台异步执行]                                               │
├─────────────────────────────────────────────────────────────┤
│  1. update_task_status(task_id, "processing")               │
│                                                              │
│  2. 初始化状态: {task_id, file_dir, import_file_path}        │
│                                                              │
│  3. 创建 KBImportWorkflow() 工作流实例                        │
│                                                              │
│  4. 流式执行: workflow.run(init_state, stream=True)          │
│     ├─ 每个节点完成时: add_done_task(task_id, node_name)     │
│     └─ 状态实时更新，前端可轮询获取                           │
│                                                              │
│  5. 完成 → update_task_status(task_id, "completed")         │
│     异常 → update_task_status(task_id, "failed")            │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 LangGraph 导入工作流节点流程

```
node_entry (检查文件类型)
       ↓ [条件路由]
    ┌───────┴───────┐
    ↓               ↓
PDF文件          MD文件
    ↓               ↓
node_pdf_to_md  node_md_img (图片处理)
    ↓               ↓
node_md_img (图片处理)
    ↓
node_document_split (文档切分)
    ↓
node_item_name_recognition (商品名称识别)
    ↓
node_bge_embedding (向量生成: BGE3)
    ↓
node_import_milvus (导入 Milvus 向量库)
    ↓
END
```

### 1.3 关键节点详解

| 节点 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `node_entry` | 判断文件类型 | `import_file_path` | `is_pdf_read_enabled`/`is_md_read_enabled`, `pdf_path`/`md_path` |
| `node_pdf_to_md` | PDF转Markdown（调用MinerU服务） | `pdf_path`, `file_dir` | `md_content`, `md_path` |
| `node_md_img` | 解析文档中的图片含义并嵌入 | `md_content` | 增强后的内容 |
| `node_document_split` | 文档切分为Chunk | markdown内容 | `chunks`列表 |
| `node_item_name_recognition` | 识别商品名称 | `chunks` | `item_names` |
| `node_bge_embedding` | BGE3向量化（稠密+稀疏向量） | `chunks` | `dense_vector`, `sparse_vector` |
| `node_import_milvus` | 数据入库Milvus | `chunks`（含向量） | `chunk_id`回填 |

### 1.4 任务状态查询 `/status/{task_id}`

前端通过轮询此接口获取实时进度：

```json
{
    "code": 200,
    "task_id": "...",
    "status": "processing",
    "done_list": ["开始上传文件", "检查文件", "PDF转Markdown"],
    "running_list": ["文档切分"]
}
```

---

## 🔍 二、Query Service（查询会话服务）

### 2.1 查询接口 `/query` 完整流程

```
前端 POST /query
       ↓
┌─────────────────────────────────────────────────────────────┐
│  query(background_tasks, request)                           │
│  参数: query, session_id, is_stream                          │
├─────────────────────────────────────────────────────────────┤
│  1. 解析参数: user_query, session_id, is_stream              │
│                                                              │
│  2. 流式模式: create_sse_queue(session_id)                   │
│                                                              │
│  3. update_task_status(session_id, TASK_STATUS_PROCESSING, is_stream)  │
│                                                              │
│  4. 分支处理:                                                 │
│     ├─ is_stream=True:                                       │
│     │   background_tasks.add_task(run_query_graph, ...)      │
│     │   返回: {"message":"处理中...", "session_id":...}       │
│     │                                                        │
│     └─ is_stream=False:                                      │
│         run_query_graph(session_id, user_query, False)       │
│         answer = get_task_result(session_id, "answer", "")   │
│         返回: {"message":"完成", "session_id":..., "answer":...}│
└─────────────────────────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────────────────────┐
│  run_query_graph(session_id, user_query, is_stream)          │
├─────────────────────────────────────────────────────────────┤
│  1. 初始化状态: {original_query, session_id, is_stream}      │
│                                                              │
│  2. 创建 KBQueryWorkflow() 工作流实例                         │
│                                                              │
│  3. 执行: workflow.run(init_state, stream=is_stream)         │
│                                                              │
│  4. 完成 → update_task_status(session_id, TASK_STATUS_COMPLETED, is_stream)  │
│     异常 → update_task_status(session_id, TASK_STATUS_FAILED, is_stream)      │
│            push_to_session(session_id, SSEEvent.ERROR, {...})                 │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 SSE 流式连接 `/stream/{session_id}`

```
前端建立 EventSource("/stream/{session_id}")
       ↓
┌─────────────────────────────────────────────────────────────┐
│  stream(session_id, request) → StreamingResponse            │
├─────────────────────────────────────────────────────────────┤
│  生成器: sse_generator(session_id, request)                  │
│  ├─ 发送: event: ready → 连接建立                            │
│  ├─ 轮询队列: stream_queue.get()                             │
│  ├─ 推送事件:                                                │
│  │   ├─ SSEEvent.PROGRESS → 节点进度更新                     │
│  │   ├─ SSEEvent.DELTA → LLM增量输出                         │
│  │   ├─ SSEEvent.FINAL → 最终答案（含图片URL）               │
│  │   └─ SSEEvent.ERROR → 错误信息                           │
│  └─ 客户端断开 → 清理队列，退出循环                           │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 LangGraph 查询工作流节点流程

```
node_item_name_confirm (确认问题产品)
       ↓ [条件路由]
    ┌─────────────────────┴─────────────────────┐
    ↓                                           ↓
有answer（反问/拒识）                     无answer（继续搜索）
    ↓                                           ↓
node_answer_output → END                node_multi_search（虚拟节点）
                                             ↓ [并发执行]
                                 ┌─────────────┼─────────────┐
                                 ↓             ↓             ↓
                        node_search_embedding  node_search_embedding_hyde  node_web_search_mcp
                        (向量搜索)             (HyDE向量搜索)            (联网搜索)
                                 ↓             ↓             ↓
                                 └─────────────┴─────────────┘
                                             ↓
                                        node_join（虚拟节点，合并结果）
                                             ↓
                                        node_rrf（倒排融合排序）
                                             ↓
                                        node_rerank（重排序）
                                             ↓
                                        node_answer_output（生成答案）
                                             ↓
                                        END
```

### 2.4 关键节点详解

| 节点 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `node_item_name_confirm` | LLM提取商品名+向量搜索对齐 | `original_query`, `session_id` | `item_names`, `rewritten_query`, `answer` |
| `node_search_embedding` | Milvus混合向量搜索（稠密+稀疏） | `item_names`, `rewritten_query` | 搜索结果 |
| `node_search_embedding_hyde` | HyDE假设性文档向量搜索 | `rewritten_query` | 搜索结果 |
| `node_web_search_mcp` | 联网搜索（调用MCP工具） | `rewritten_query` | 网络结果 |
| `node_rrf` | Reciprocal Rank Fusion倒排融合 | 多路搜索结果 | 融合排序结果 |
| `node_rerank` | CrossEncoder重排序 | RRF结果 | `reranked_docs` |
| `node_answer_output` | LLM生成最终答案（支持流式） | `reranked_docs`, `history` | `answer`, `image_urls` |

### 2.5 `node_item_name_confirm` 核心逻辑

```
步骤1: 参数校验 (session_id, original_query)
       ↓
步骤2: 获取MongoDB历史记录
       ↓
步骤3: 保存用户初始消息到MongoDB
       ↓
步骤4: LLM提取 item_names + 改写 query
       ↓
步骤5: item_names向量化 + Milvus混合搜索
       ↓
步骤6: 商品名对齐（评分>0.85确认，0.65-0.85候选）
       ↓
步骤7: 分支判断:
       ├─ 有确认商品 → 更新state["item_names"]，继续搜索
       ├─ 有候选商品 → 生成反问句写入state["answer"]，直接输出
       └─ 无结果 → 生成拒识回复写入state["answer"]，直接输出
       ↓
步骤8: 写入会话历史到MongoDB
```

---

## 🗂️ 三、共享工具模块

| 模块 | 文件 | 功能 |
|------|------|------|
| 任务管理 | `utils/task_utils.py` | 内存态任务追踪（running/done/status/result） |
| SSE管理 | `utils/sse_utils.py` | 会话队列、事件推送、流式生成器 |
| MinIO操作 | `utils/minio_utils.py` | 对象存储客户端、上传/下载 |
| Milvus操作 | `utils/milvus_utils.py` | 向量数据库客户端、混合搜索 |
| 历史记录 | `utils/mongo_history_utils.py` | MongoDB会话管理 |
| LLM工具 | `utils/llm_utils.py` | 大语言模型客户端 |
| 嵌入工具 | `utils/embedding_utils.py` | BGE3向量生成 |

---

## 🔗 四、数据流向总览

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          掌柜智库数据流向                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐    /upload    ┌─────────────┐    LangGraph    ┌──────────────┐ │
│  │   前端上传   │ ───────────→ │ import_service│ ────────────→ │  MinIO +     │ │
│  │  (PDF/MD)   │              │ (8000端口)    │              │   Milvus     │ │
│  └─────────────┘              └─────────────┘              └──────────────┘ │
│                                                                                 │
│  ┌─────────────┐    /query     ┌─────────────┐    LangGraph    ┌──────────────┐ │
│  │   前端查询   │ ───────────→ │ query_service│ ────────────→ │  Milvus +    │ │
│  │  (自然语言)  │   /stream    │ (8001端口)    │              │   Web +      │ │
│  └─────────────┘ ←─────────────┘              │              │   LLM        │ │
│                  SSE实时推送                   └─────────────┘              └──────┘ │
│                                                     │                              │
│                                                     ↓                              │
│                                              ┌──────────────┐                     │
│                                              │   MongoDB    │                     │
│                                              │  (会话历史)   │                     │
│                                              └──────────────┘                     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ 五、服务配置与启动

### 5.1 服务端口

| 服务 | 文件 | 端口 | 启动命令 |
|------|------|------|----------|
| Import Service | `web/api/import_service.py` | 8000 | `python web/api/import_service.py` |
| Query Service | `web/api/query_service.py` | 8001 | `python web/api/query_service.py` |

### 5.2 核心配置文件

| 配置文件 | 用途 |
|----------|------|
| `config/minio_config.py` | MinIO 对象存储配置 |
| `config/milvus_config.py` | Milvus 向量库配置 |
| `config/lm_config.py` | 大语言模型配置 |
| `config/embedding_config.py` | BGE3 嵌入模型配置 |
| `config/mineru_config.py` | MinerU PDF解析服务配置 |

---

## 📝 六、API 接口汇总

### 6.1 Import Service (端口 8000)

| 接口 | 方法 | 描述 |
|------|------|------|
| `/upload` | POST | 文件上传（支持多文件，form-data格式） |
| `/status/{task_id}` | GET | 查询任务状态与进度 |
| `/import.html` | GET | 返回导入前端页面 |

### 6.2 Query Service (端口 8001)

| 接口 | 方法 | 描述 |
|------|------|------|
| `/query` | POST | 发起查询请求（支持流式） |
| `/stream/{session_id}` | GET | SSE 流式响应 |
| `/history/{session_id}` | GET | 查询会话历史 |
| `/history/{session_id}` | DELETE | 清空会话历史 |
| `/health` | GET | 健康检查 |
| `/chat.html` | GET | 返回聊天前端页面 |

---

## 📌 七、关键设计要点

### 7.1 异步处理模式
- **导入服务**：文件上传后立即返回，LangGraph流程在后台任务中异步执行
- **查询服务**：流式模式下，查询请求立即返回，结果通过SSE实时推送

### 7.2 任务状态管理
- 内存态字典存储任务状态，高性能无IO
- 支持四种状态：pending → processing → completed/failed
- 节点进度实时更新，前端可轮询或通过SSE接收

### 7.3 SSE 事件类型
| 事件类型 | 用途 | 触发时机 |
|----------|------|----------|
| `SSEEvent.READY` | 连接建立确认 | SSE连接成功时 |
| `SSEEvent.PROGRESS` | 节点进度更新 | 节点完成时 |
| `SSEEvent.DELTA` | LLM增量输出 | LLM流式生成时 |
| `SSEEvent.FINAL` | 最终答案 | 回答生成完成时 |
| `SSEEvent.ERROR` | 错误信息 | 流程异常时 |

### 7.4 向量搜索策略
- **混合搜索**：稠密向量（BGE3 dense）+ 稀疏向量（BGE3 sparse）
- **多路搜索**：普通向量搜索 + HyDE假设性搜索 + 联网搜索
- **排序融合**：RRF（倒排融合）→ CrossEncoder重排序

---

*文档生成时间：2026-07-08*