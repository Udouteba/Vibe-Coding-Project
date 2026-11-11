"""输入意图分类：区分问候/无关/模糊/正常查询，决定是否走检索。"""

import json

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from config import settings

INTENT_PROMPT = """判断用户输入属于哪一类，只输出 JSON（不要多余文字）：
- greeting：问候/寒暄（如"你好""在吗""谢谢"）
- off_topic：与给排水设计规范完全无关（如"今天天气""帮我写代码"）
- vague：与规范相关但过于模糊/不完整（如"消防""那个水池"）
- query：明确的规范技术问题（如"室外消火栓间距要求"）

输出格式：{"category": "greeting|vague|query|off_topic", "clarify": "仅 vague 时给出追问澄清话术，否则空字符串"}
"""

GREETING_REPLY = "你好！我是给排水规范问答助手，可回答给排水设计规范、条文等问题，请直接描述你想查询的规范内容。"
OFF_TOPIC_REPLY = "抱歉，我只能回答给排水设计规范相关的问题。请描述与给排水规范、条文相关的内容。"

_VALID_CATEGORIES = ("greeting", "off_topic", "vague", "query")


def _build_classifier() -> ChatOpenAI:
    return ChatOpenAI(
        base_url=settings.LLM_BASE_URL,
        api_key=settings.LLM_API_KEY,
        model=settings.LLM_MODEL_NAME,
        temperature=0,
        extra_body={"thinking": {"type": "disabled"}},
    )


async def classify_intent(text: str) -> dict:
    """LLM 分类用户输入意图，返回 {"category": str, "clarify": str}。"""
    llm = _build_classifier()
    resp = await llm.ainvoke(
        [SystemMessage(content=INTENT_PROMPT), HumanMessage(content=text)]
    )
    content = resp.content if isinstance(resp.content, str) else str(resp.content)
    return _parse_intent(content)


def _parse_intent(content: str) -> dict:
    """解析分类结果；解析失败或类别非法时按正常查询兜底。"""
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return {"category": "query", "clarify": ""}
    if not isinstance(data, dict):
        return {"category": "query", "clarify": ""}
    category = data.get("category")
    if category not in _VALID_CATEGORIES:
        return {"category": "query", "clarify": ""}
    return {"category": category, "clarify": data.get("clarify", "") or ""}
