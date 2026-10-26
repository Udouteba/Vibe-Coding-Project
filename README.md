# 给排水智库

面向给水排水设计规范的企业级 RAG 知识库问答系统。上传规范文档后，即可通过浏览器进行带引文出处的知识库问答，每个回答标注引用片段出自哪份规范、哪个章节/条款。

## 技术栈

- **前端**：Vue 3 + Element Plus + Axios + Vite
- **后端**：FastAPI + SQLAlchemy（异步）+ JWT
- **AI 链路**：LangChain / LangGraph + DeepSeek（`create_react_agent` + 检索工具）
- **向量化**：本地 BGE 中文模型（`BAAI/bge-small-zh-v1.5`，sentence-transformers）
- **向量库**：ChromaDB（按专业分片，本地持久化）
- **存储**：MySQL

## 目录结构

```
给排水智库APP/
├─ backend/                 # FastAPI 后端
│  ├─ .env.example          # 配置样例（复制为 .env）
│  ├─ requirements.txt
│  ├─ config.py             # pydantic-settings 读取 .env
│  ├─ sql/backend.sql       # 建库建表脚本 + 演示账号
│  └─ app/
│     ├─ main.py            # 入口：建表 / 路由 / 静态文件 / 演示账号
│     ├─ api/               # 路由层（auth/users/documents/chat/conversations/presets/categories）
│     ├─ services/          # 业务层（rag/agent/document/vector_store/conversation/...）
│     ├─ models/            # SQLAlchemy 模型
│     ├─ schemas/           # Pydantic 请求/响应
│     ├─ common/            # 统一返回 + 全局异常
│     ├─ dependencies/      # JWT 鉴权
│     └─ utils/             # jwt / password / citation
└─ frontend/                # Vue 3 前端
   └─ src/
      ├─ api/               # 接口封装
      ├─ views/             # Chat / Knowledge / Users / Profile / Login / Register
      ├─ components/        # AnswerView / SourceCollapse / ScopePanel / ConversationSidebar / ...
      ├─ layouts/           # Layout.vue（侧栏按角色显隐）
      ├─ router/  utils/    # request.js 拦截器、auth.js localStorage
      └─ styles/
```

## 环境要求

- Python 3.12+
- Node.js 18+
- MySQL 8.0+

## 启动步骤

### 1. 初始化数据库

```sql
CREATE DATABASE drainage DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

> 建表与演示账号无需手动执行：应用启动时通过 `Base.metadata.create_all` 自动建表，并自动播种演示账号。
> 也可以手动执行 `backend/sql/backend.sql`（含完整 DDL 与演示账号）。

### 2. 后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env      # 填写 DATABASE_URL / LLM_API_KEY 等
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- 健康检查：<http://127.0.0.1:8000/>
- 接口文档：<http://127.0.0.1:8000/docs>

> 首次启动会下载 BGE embedding 模型（约 400MB），请耐心等待。

### 3. 前端

```powershell
cd frontend
npm install
npm run dev       # http://127.0.0.1:5173
```

访问 <http://127.0.0.1:5173>，用演示账号登录。

## 演示账号

| 用户名 | 密码 | 角色 |
| --- | --- | --- |
| `admin` | `admin` | 管理员（知识库管理 / 用户管理） |
| `aaa` | `123` | 普通用户 |
| `bbb` | `123` | 普通用户 |

页面自行注册的用户角色固定为 `student`。

## 使用流程

1. 用 `admin` 登录，进入「知识库管理」上传规范文档（txt / md / pdf / docx），填写规范名、编号、版本、专业分类。
2. 上传完成后状态变为「已就绪」，即被即时索引，可立即检索。
3. 进入「智能问答」，在右上角「检索范围」里勾选要提问的规范（支持专业分组、搜索、版本标识、多选、存预设）。
4. 提问后，回答中的 `[N]` 标注可点击溯源、悬停预览原文、一键复制引用格式，正文下方有可折叠的原文引用块。

## 关键设计说明

- **RAG 链路**：LangChain 文档加载 → `RecursiveCharacterTextSplitter` 中文切分（含条款号分隔符）→ BGE 向量化 → ChromaDB 检索 → `create_react_agent`（DeepSeek + `search_regulations` 工具）组织回答。
- **引用溯源**：检索结果按相关度排序，模型以 `[N]` 标注引用，N 与前端 citations 数组一一对应；后端把规范名/编号/版本/章节/条款写入分片元数据。
- **公式问题**：系统提示词强制「只给公式、不做计算」，并明确声明「本回答仅提供公式，不做计算」。
- **资料不足**：检索结果为空或最高相关度低于 `RETRIEVE_MIN_SCORE` 时标记低置信，模型回答「资料不足，无法回答」。
- **性能优化**：SQLAlchemy 异步引擎 + 连接池；向量检索 LRU 缓存（query+范围 为 key）；ChromaDB 按专业分 collection（索引分片）；SSE 流式输出；阻塞的 embedding/LLM 调用走 `asyncio.to_thread`。
- **权限隔离**：知识库管理、用户管理仅 admin；问答、会话、预设面向所有登录用户；多用户会话按 `user_id` 隔离，历史对话持久化可跨登录找回。

## 部署注意事项

- 生产环境请用 `npm run build` 产出 `frontend/dist`，由 Nginx 托管，并将 `/api`、`/uploads` 反向代理到后端 8000。
- `.env` 含本地密钥，**不要提交**；对外分享用 `.env.example` 占位。
- 后端 `data/chroma`（向量库）与 `uploads/`（原始文件）需持久化备份；向量库丢失可通过「重新索引」从原始文件重建。
