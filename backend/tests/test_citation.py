"""引用工具：章节 / 条款提取与格式化。"""

from app.utils.citation import extract_chapter, extract_clause, format_citation, split_clauses


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


def test_split_clauses_basic():
    pages = [{"page": 1, "text": "5.2.5 管井结构\n\n5.2.6 管井井口"}]
    chunks = split_clauses(pages)
    assert [c["clause"] for c in chunks] == ["5.2.5", "5.2.6"]
    assert all(c["page"] == "1" for c in chunks)


def test_split_clauses_title_metadata():
    pages = [{"page": 1, "text": "5 取水构筑物\n5.2 管井\n5.2.5 管井结构应符合规定。"}]
    chunks = split_clauses(pages)
    assert len(chunks) == 1
    assert chunks[0]["chapter"] == "5 取水构筑物"
    assert chunks[0]["section"] == "5.2 管井"
    assert chunks[0]["clause"] == "5.2.5"


def test_split_clauses_skip_front_matter():
    pages = [{"page": 1, "text": "前言\n这是前言内容\n5 总则\n5.1.1 条文内容"}]
    chunks = split_clauses(pages)
    assert len(chunks) == 1
    assert chunks[0]["clause"] == "5.1.1"


def test_split_clauses_page_range():
    pages = [
        {"page": 5, "text": "5.2.5 条文开头"},
        {"page": 6, "text": "条文续内容"},
        {"page": 6, "text": "5.2.6 下一条"},
    ]
    chunks = split_clauses(pages)
    assert chunks[0]["page"] == "5-6"
    assert chunks[1]["page"] == "6"


def test_split_clauses_table_flag():
    pages = [{"page": 1, "text": "5.2.10 条文内容\n表 5.2.10-A 参数表\n| a | b |"}]
    chunks = split_clauses(pages)
    assert chunks[0]["has_table"] is True


def test_split_clauses_long_split():
    text = "5.2.5 " + "。".join(f"第{i}句内容" for i in range(60))
    pages = [{"page": 1, "text": text}]
    chunks = split_clauses(pages, max_chars=100)
    assert len(chunks) > 1
    assert all(c["clause"] == "5.2.5" for c in chunks)
