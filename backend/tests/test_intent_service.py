"""意图分类纯函数测试（mock LLM）。"""

import json

from app.services import intent_service


def test_parse_intent_query():
    data = intent_service._parse_intent(json.dumps({"category": "query", "clarify": ""}))
    assert data == {"category": "query", "clarify": ""}


def test_parse_intent_vague_with_clarify():
    data = intent_service._parse_intent(
        json.dumps({"category": "vague", "clarify": "请问您想了解哪方面？"})
    )
    assert data == {"category": "vague", "clarify": "请问您想了解哪方面？"}


def test_parse_intent_greeting():
    data = intent_service._parse_intent(json.dumps({"category": "greeting", "clarify": ""}))
    assert data == {"category": "greeting", "clarify": ""}


def test_parse_intent_invalid_json_fallback():
    assert intent_service._parse_intent("这不是JSON") == {"category": "query", "clarify": ""}


def test_parse_intent_invalid_category_fallback():
    data = intent_service._parse_intent(json.dumps({"category": "unknown", "clarify": "x"}))
    assert data == {"category": "query", "clarify": ""}


class _FakeLLM:
    def __init__(self, content: str):
        self._content = content

    async def ainvoke(self, messages):
        class _Resp:
            content = self._content

        return _Resp()


async def test_classify_intent_off_topic(monkeypatch):
    monkeypatch.setattr(
        intent_service,
        "_build_classifier",
        lambda: _FakeLLM('{"category": "off_topic", "clarify": ""}'),
    )
    result = await intent_service.classify_intent("今天天气")
    assert result["category"] == "off_topic"


async def test_classify_intent_bad_json_fallback(monkeypatch):
    monkeypatch.setattr(intent_service, "_build_classifier", lambda: _FakeLLM("不是JSON"))
    result = await intent_service.classify_intent("随便")
    assert result == {"category": "query", "clarify": ""}
