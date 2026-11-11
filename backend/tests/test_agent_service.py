"""Agent 纯函数单元测试（不加载模型）。"""

import json

from langchain_core.messages import AIMessage, HumanMessage

from app.models import Message
from app.services.agent_service import _build_messages, _extract_text, _make_search_tool, _sse


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
    assert msgs[2].content == "<user_input>\n新问\n</user_input>"


def test_make_search_tool_empty(monkeypatch):
    monkeypatch.setattr(
        "app.services.agent_service.rag_service.retrieve", lambda q, d, k=None: []
    )
    tool, collected = _make_search_tool([])
    assert "未检索到" in tool.invoke({"query": "anything"})
    assert collected == []


def test_make_search_tool_formats(monkeypatch):
    items = [
        {
            "document_id": 1,
            "title": "规范",
            "code": "GB 50015",
            "version": "2019",
            "chapter": "第一章",
            "clause": "1.1",
            "content": "条文内容",
        }
    ]
    monkeypatch.setattr(
        "app.services.agent_service.rag_service.retrieve", lambda q, d, k=None: items
    )
    tool, collected = _make_search_tool([])
    out = tool.invoke({"query": "anything"})
    assert "[1]" in out and "条文内容" in out
    assert len(collected) == 1
    assert collected[0]["cite_id"] == 1


def test_make_search_tool_dedup(monkeypatch):
    items = [{"document_id": 1, "clause": "1.1", "content": "条文内容"}]
    monkeypatch.setattr(
        "app.services.agent_service.rag_service.retrieve", lambda q, d, k=None: items
    )
    tool, collected = _make_search_tool([])
    tool.invoke({"query": "q1"})
    out = tool.invoke({"query": "q2"})  # 相同条文，应去重，不重复编号
    assert "未检索到" in out
    assert len(collected) == 1


def test_make_search_tool_global_numbering(monkeypatch):
    items = [
        [{"document_id": 1, "clause": "1.1", "content": "甲"}],
        [{"document_id": 1, "clause": "1.2", "content": "乙"}],
    ]
    calls = {"n": 0}

    def fake_retrieve(q, d, k=None):
        result = items[calls["n"]]
        calls["n"] += 1
        return result

    monkeypatch.setattr(
        "app.services.agent_service.rag_service.retrieve", fake_retrieve
    )
    tool, collected = _make_search_tool([])
    tool.invoke({"query": "q1"})
    tool.invoke({"query": "q2"})
    assert [c["cite_id"] for c in collected] == [1, 2]
