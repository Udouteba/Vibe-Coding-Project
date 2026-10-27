"""Agent + SSE 流式问答。

链路：预检索（取回条文 + 引用编号）→ LangGraph create_react_agent
（ChatOpenAI/DeepSeek + search_regulations 工具）→ SSE 流式输出。
"""

import asyncio
import json
from typing import AsyncGenerator

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from config import settings

from ..database import SessionLocal
from ..models import Message
from ..schemas.chat import ChatRequest
from . import conversation_service, document_service, rag_service

SYSTEM_PROMPT = """你是「给排水智库」的规范问答助手，只能依据检索工具返回的给排水设计规范条文作答，严禁编造。
要求：
1. 先调用 search_regulations 工具检索相关条文，再基于条文作答。
2. 每个关键结论后用 [N] 标注引用，N 对应检索结果中的编号（如 [1]、[2]）。
3. 若检索结果不足或与问题无关，必须明确回答「资料不足，无法回答」，不要硬编。
4. 使用简体中文，回答结构清晰、条理分明。
5. 当用户询问需要套用公式做数学计算的问题时，只给出相关公式本身，不进行数值计算，并明确说明「本回答仅提供公式，不做计算」。
"""


def _build_llm() -> ChatOpenAI:
    return ChatOpenAI(
        base_url=settings.LLM_BASE_URL,
        api_key=settings.LLM_API_KEY,
        model=settings.LLM_MODEL_NAME,
        temperature=settings.LLM_TEMPERATURE,
        streaming=True,
        extra_body={"thinking": {"type": "disabled"}},
    )


def _make_tool(retrieved: list[dict]):
    @tool
    def search_regulations(query: str) -> str:
        """检索给排水设计规范，返回相关条文及引用编号。"""
        if not retrieved:
            return "未检索到任何相关规范条文。"
        parts = []
        for i, item in enumerate(retrieved, 1):
            head = (
                f"[{i}] 《{item.get('title', '')}》{item.get('code', '')}"
                f"（{item.get('version', '')}版）{item.get('chapter', '')} {item.get('clause', '')}"
            )
            parts.append(f"{head}\n{item.get('content', '')}")
        return "\n\n".join(parts)

    return search_regulations


def _build_messages(history: list[Message], user_text: str):
    msgs = []
    for m in history:
        if m.role == "user":
            msgs.append(HumanMessage(content=m.content))
        elif m.role == "assistant":
            msgs.append(AIMessage(content=m.content))
    msgs.append(HumanMessage(content=user_text))
    return msgs


def _extract_text(content) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for c in content:
            if isinstance(c, str):
                parts.append(c)
            elif isinstance(c, dict):
                parts.append(c.get("text") or "")
        return "".join(parts)
    return str(content)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def stream_ask(user_id: int, req: ChatRequest) -> AsyncGenerator[str, None]:
    if not settings.LLM_API_KEY:
        yield _sse("error", {"message": "未配置 LLM_API_KEY"})
        return

    # 1. 建会话 / 存用户消息 / 加载历史与检索范围
    async with SessionLocal() as db:
        conv = await conversation_service.get_or_create(
            db, user_id, req.conversation_id, req.message
        )
        history = await conversation_service.list_messages(db, conv.id)
        user_msg = Message(conversation_id=conv.id, role="user", content=req.message)
        db.add(user_msg)
        await db.commit()
        scope_docs = await document_service.load_scope_docs(db, req.document_ids)

    # 2. 预检索（保证引用编号与前端 citations 数组一一对应）
    retrieved = await asyncio.to_thread(rag_service.retrieve, req.message, scope_docs)
    low_confidence = rag_service.compute_low_confidence(retrieved)

    agent = create_react_agent(_build_llm(), [_make_tool(retrieved)], prompt=SYSTEM_PROMPT)

    answer = ""
    error_msg: str | None = None
    try:
        messages = _build_messages(history, req.message)
        async for event in agent.astream_events(
            {"messages": messages},
            config={"recursion_limit": settings.AGENT_RECURSION_LIMIT},
            version="v2",
        ):
            kind = event.get("event")
            if kind == "on_chat_model_stream":
                text = _extract_text(event["data"]["chunk"].content)
                if text:
                    answer += text
                    yield _sse("token", {"content": text})
            elif kind == "on_tool_start":
                yield _sse("tool_start", {"name": event.get("name")})
            elif kind == "on_tool_end":
                yield _sse("tool_end", {"name": event.get("name")})
    except Exception as e:
        error_msg = str(e)

    # 3. 持久化助手消息
    async with SessionLocal() as db:
        am = Message(
            conversation_id=conv.id,
            role="assistant",
            content=answer,
            citations=retrieved,
            low_confidence=low_confidence,
        )
        db.add(am)
        await db.commit()
        await db.refresh(am)
        await conversation_service.touch(db, conv.id)

    if error_msg:
        yield _sse("error", {"message": f"生成失败: {error_msg}", "conversation_id": conv.id})
    else:
        yield _sse("citations", {"items": retrieved})
        yield _sse(
            "done",
            {
                "conversation_id": conv.id,
                "message_id": am.id,
                "low_confidence": low_confidence,
                "citations": retrieved,
            },
        )
