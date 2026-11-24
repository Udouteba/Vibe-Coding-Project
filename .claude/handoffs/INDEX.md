# Handoff 索引

给排水智库（`C:\Users\86189\Desktop\给排水智库APP`）——面向给排水设计规范的企业级 RAG 知识库问答系统。
技术栈：FastAPI + SQLAlchemy 异步 + JWT · Vue3 + Element Plus · LangChain/LangGraph + DeepSeek · ChromaDB + BGE embedding · MySQL。

> 用法：新会话先读本索引定位历史决策，再按「日志文件」找到对应交接文档，按「项目文件地图」读取具体代码。

## 日志文件（按时间倒序）

| 日志 | 主题 | 状态 |
| --- | --- | --- |
| [2026-11-24-大文件OCR重构与公式识别.md](./2026-11-24-大文件OCR重构与公式识别.md) | 上传异步化 + 分批 OCR（子进程隔离/断点续传/进度）+ 公式识别 + 内联清洗 | 已合并 main 并推送 |
| [2026-11-11-六方案编码完成与实测.md](./2026-11-11-六方案编码完成与实测.md) | 六方案（OCR/切块/真工具检索/Rerank/意图路由/注入防护）编码 + 端到端实测 + 依赖踩坑 | 已编码，未提交 |
| [2026-11-08-RAG提示词注入防护方案.md](./2026-11-08-RAG提示词注入防护方案.md) | 提示词注入防护（prompt 强化 + delimiter + 注入过滤） | 已编码 |
| [2026-11-08-RAG输入意图路由方案.md](./2026-11-08-RAG输入意图路由方案.md) | 输入意图路由（LLM 分类 + 模糊边界处理） | 已编码 |
| [2026-11-04-RAG检索重排Rerank方案.md](./2026-11-04-RAG检索重排Rerank方案.md) | 检索 Rerank 重排（bge-reranker-base，召回20→精排6） | 已编码 |
| [2026-11-04-RAG对话真工具检索方案.md](./2026-11-04-RAG对话真工具检索方案.md) | 对话模块真工具检索改造（多轮追问 + 引用编号去重） | 已编码 |
| [2026-11-04-RAG切块方案.md](./2026-11-04-RAG切块方案.md) | RAG 条文语义切块方案 + 规范归属溯源 | 已编码 |
| [2026-11-04-扫描件OCR与表格解析方案.md](./2026-11-04-扫描件OCR与表格解析方案.md) | 扫描件 OCR + 表格解析方案（PaddleOCR/PP-Structure） | 已编码 |
| [2026-11-04-前后端单元测试与规范审查.md](./2026-11-04-前后端单元测试与规范审查.md) | 前后端单元测试 + 规范审查修复 + 测试 subagent | 已合并 main 并推送 |
| [2026-10-27-bugfix-权限主题与账号密码校验.md](./2026-10-27-bugfix-权限主题与账号密码校验.md) | 权限 / 主题按账号记住 / 账号密码规则校验 | 已合并 main 并推送 |
| [2026-10-27-给排水智库-RAG系统开发完成.md](./2026-10-27-给排水智库-RAG系统开发完成.md) | RAG 系统开发完成 | 已完成 |

## 项目文件地图

### 后端 `backend/`
- `config.py` — 配置（LLM/DB/JWT/HF 镜像/embedding/OCR/Rerank/切块）
- `app/main.py` — 入口：建表、`_ensure_theme_column`/`_ensure_chunk_columns`/`_ensure_document_progress_columns` 迁移、演示账号播种、路由挂载
- `app/api/` — 路由层：`auth` `users` `chat` `documents` `conversations` `presets` `categories`
- `app/services/` — 业务：`agent_service`（RAG+SSE+意图路由+注入防护）、`document_service`（OCR/语义切块）、`vector_store_service`（检索+Rerank）、`rag_service`、`ocr_service`（扫描件 OCR）、`intent_service`（意图分类）、`auth_service`、`user_service`、`conversation_service`、`preset_service`
- `app/ocr_worker.py` — OCR 子进程入口（独立加载 paddle，逐页 OCR 写 jsonl 断点续传，与 embedding 的 torch 隔离）
- `app/models/` — ORM：`user` / `document`（含 chunk，chunk 带 section/page）/ `conversation`（含 message）/ `preset`
- `app/schemas/` — Pydantic 请求/响应
- `app/utils/` — `validators.py`、`password.py`、`jwt.py`、`citation.py`（split_clauses 语义切块）、`injection_guard.py`（注入过滤）、`latex_clean.py`（内联 LaTeX 清洗）
- `app/dependencies/auth.py` — JWT 鉴权（`get_current_user` / `get_current_admin`）
- `app/common/` — 统一 `Response` + 全局异常处理
- `sql/backend.sql` — 建库建表脚本（含演示账号）

### 前端 `frontend/src/`
- `views/Chat.vue` — 核心问答页（会话侧栏 + 检索范围 + SSE 流式）
- `views/Knowledge.vue` — 知识库管理（admin）
- `views/Users.vue` — 用户管理（admin，禁止编辑自己）
- `views/Login.vue` / `Register.vue` / `Profile.vue` — 登录 / 注册 / 个人中心
- `components/` — `ThemeToggle`（主题）、`AnswerView`（引用渲染）、`ScopePanel`（检索范围）、`ConversationSidebar`、`SourceCollapse`、`SuggestionBar`
- `utils/` — `validators.js`（校验）、`theme.js`（主题）、`request.js`（axios 拦截器）、`auth.js`（token/userInfo）、`citation.js`
- `api/` — 接口封装（auth/users/chat/documents/conversations/presets/categories）
- `router/index.js` — 路由 + 守卫 · `layouts/Layout.vue` — 侧栏菜单（按角色显隐）

## 快速上手

```powershell
# 后端（8000）
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 前端（5173）
cd frontend
npm run dev
```

- Swagger：`http://127.0.0.1:8000/docs`
- 演示账号：`admin/admin`（管理员）、`aaa/123`、`bbb/123`（学生，启动自动播种）

## 测试

- 后端：`cd backend && python -m pytest tests -v`；规范 `ruff check .`
- 前端：`cd frontend && npm test`
- 可复用测试 subagent：
  - `backend-tests`（`.claude/agents/backend-tests.md`）—— 按后端代码变更补/改 pytest 测试
  - `frontend-tests`（`.claude/agents/frontend-tests.md`）—— 按前端代码变更补/改 Vitest 测试

## 关键约定

- 账号密码校验前后端必须一致：`backend/app/utils/validators.py` ↔ `frontend/src/utils/validators.js`
- 主题按账号存 `users.theme`，迁移在 `app/main.py::_ensure_theme_column`
- 分片溯源字段 `section/page` 存 `document_chunks`，迁移在 `app/main.py::_ensure_chunk_columns`
- OCR/Rerank 依赖版本已锁定（`requirements.txt`），勿轻易升级 paddle/paddleocr/numpy——踩坑详见 [[2026-11-11-六方案编码完成与实测]]
- 扫描件 OCR 在独立子进程跑（`app/ocr_worker.py`），与 embedding(torch) 隔离避免 OpenMP 冲突段错误；分批配置 `OCR_BATCH_SIZE=20`/`OCR_AUTO_SPLIT_THRESHOLD=30`，断点续传 jsonl 存 `uploads/{doc_id}.ocr.jsonl`
- 公式识别已开启（`use_formula_recognition=True`）：公式块（formula label）保留 LaTeX，正文内联 `$...$` 由 `latex_clean.clean_inline_latex` 清洗；paddle 公式识别须用 `np.array`（`np.asarray(PIL.Image)` 只读会崩）
- Rerank 只排序、score 保留 cosine（`RETRIEVE_MIN_SCORE` 阈值语义不变）
- 新增模型须在 `app/models/__init__.py` import（触发 `create_all` 建表）
- 测试套件：后端 pytest（`backend/tests/`）+ ruff，前端 Vitest（`frontend/tests/`），详见下方「测试」
