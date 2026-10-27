"""Agent 纯函数单元测试（不加载模型）。"""

import json

from langchain_core.messages import AIMessage, HumanMessage

from app.models import Message
from app.services.agent_service import _build_messages, _extract_text, _make_tool, _sse


def test_extract_text_str():
    assert _extract_text("你好") == "你好"


def test_extract_text_none():
    assert _extract_text(None) == ""


def test_extract_text_list():
    assert _extract_text(["a", {"text": "b"}, {"other": "x"}]) == "ab"


def test_sse():
    out = _sse("token", {"content": "hi"})
    assert out.startswith("event: token\n")
    payload = out.split("data: ", 1)[1].strip()
    assert json.loads(payload) == {"content": "hi"}


def test_build_messages():
    history = [Message(role="user", content="问"), Message(role="assistant", content="答")]
    msgs = _build_messages(history, "新问")
    assert isinstance(msgs[0], HumanMessage)
    assert isinstance(msgs[1], AIMessage)
    assert isinstance(msgs[2], HumanMessage)
    assert msgs[2].content == "新问"


def test_make_tool_empty():
    tool = _make_tool([])
    assert "未检索到" in tool.invoke({"query": "anything"})


def test_make_tool_formats():
    retrieved = [
        {
            "title": "规范",
            "code": "GB 50015",
            "version": "2019",
            "chapter": "第一章",
            "clause": "1.1",
            "content": "条文内容",
        }
    ]
    tool = _make_tool(retrieved)
    out = tool.invoke({"query": "anything"})
    assert "[1]" in out and "条文内容" in out


def test_make_tool_missing_keys():
    tool = _make_tool([{}])  # 缺 key 不应抛 KeyError
    assert "[1]" in tool.invoke({"query": "anything"})
