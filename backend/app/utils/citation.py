"""引用相关工具：从条文文本中提取章节/条款号、格式化引用。"""

import re

CHAPTER_RE = re.compile(r"第[零〇一二三四五六七八九十百0-9]+章")
ARTICLE_RE = re.compile(r"第[零〇一二三四五六七八九十百0-9]+条")
CLAUSE_RE = re.compile(r"\d+(?:\.\d+){1,3}")


def extract_chapter(text: str) -> str:
    m = CHAPTER_RE.search(text)
    return m.group(0) if m else ""


def extract_clause(text: str) -> str:
    m = ARTICLE_RE.search(text)
    if m:
        return m.group(0)
    m = CLAUSE_RE.search(text)
    return m.group(0) if m else ""


def format_citation(item: dict) -> str:
    """格式化为「《规范名》编号（版本）章节 条款」。"""
    s = f"《{item.get('title', '')}》"
    if item.get("code"):
        s += f" {item['code']}"
    if item.get("version"):
        s += f"（{item['version']}版）"
    if item.get("chapter"):
        s += f" {item['chapter']}"
    if item.get("clause"):
        s += f" {item['clause']}"
    return s
