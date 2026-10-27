# Handoff 索引

给排水智库（`C:\Users\86189\Desktop\给排水智库APP`）——面向给排水设计规范的企业级 RAG 知识库问答系统。
技术栈：FastAPI + SQLAlchemy 异步 + JWT · Vue3 + Element Plus · LangChain/LangGraph + DeepSeek · ChromaDB + BGE embedding · MySQL。

> 用法：新会话先读本索引定位历史决策，再按「日志文件」找到对应交接文档，按「项目文件地图」读取具体代码。

## 日志文件（按时间倒序）

| 日志 | 主题 | 状态 |
| --- | --- | --- |
| [2026-10-27-bugfix-权限主题与账号密码校验.md](./2026-10-27-bugfix-权限主题与账号密码校验.md) | 权限 / 主题按账号记住 / 账号密码规则校验 | 已合并 main 并推送 |
| [2026-10-27-给排水智库-RAG系统开发完成.md](./2026-10-27-给排水智库-RAG系统开发完成.md) | RAG 系统开发完成 | 已完成 |

## 项目文件地图

### 后端 `backend/`
- `config.py` — 配置（LLM/DB/JWT/HF 镜像/embedding）
- `app/main.py` — 入口：建表、`_ensure_theme_column` 迁移、演示账号播种、路由挂载
- `app/api/` — 路由层：`auth` `users` `chat` `documents` `conversations` `presets` `categories`
- `app/services/` — 业务：`agent_service`（RAG+SSE）、`document_service`、`vector_store_service`、`rag_service`、`auth_service`、`user_service`、`conversation_service`、`preset_service`
- `app/models/` — ORM：`user` / `document`（含 chunk）/ `conversation`（含 message）/ `preset`
- `app/schemas/` — Pydantic 请求/响应
- `app/utils/` — `validators.py`（账号密码规则）、`password.py`、`jwt.py`、`citation.py`
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
- 新增模型须在 `app/models/__init__.py` import（触发 `create_all` 建表）
- 测试套件：后端 pytest（`backend/tests/`）+ ruff，前端 Vitest（`frontend/tests/`），详见下方「测试」
