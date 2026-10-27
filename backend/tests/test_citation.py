"""引用工具：章节 / 条款提取与格式化。"""

from app.utils.citation import extract_chapter, extract_clause, format_citation


def test_extract_chapter():
    assert extract_chapter("第一章 总则") == "第一章"
    assert extract_chapter("第3章 给水") == "第3章"
    assert extract_chapter("无章节内容") == ""


def test_extract_clause_article():
    assert extract_clause("第一条 目的") == "第一条"
    assert extract_clause("第12条 规定") == "第12条"


def test_extract_clause_number():
    assert extract_clause("3.1.2 条文") == "3.1.2"


def test_format_citation_full():
    item = {
        "title": "建筑给水排水设计标准",
        "code": "GB 50015",
        "version": "2019",
        "chapter": "第三章",
        "clause": "3.1.2",
    }
    assert format_citation(item) == "《建筑给水排水设计标准》 GB 50015（2019版） 第三章 3.1.2"


def test_format_citation_minimal():
    assert format_citation({"title": "规范"}) == "《规范》"
