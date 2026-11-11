"""引用相关工具：提取章节/条款号、语义条文切块、格式化引用。"""

import re

from langchain_text_splitters import RecursiveCharacterTextSplitter

CHAPTER_RE = re.compile(r"第[零〇一二三四五六七八九十百0-9]+章")
ARTICLE_RE = re.compile(r"第[零〇一二三四五六七八九十百0-9]+条")
CLAUSE_RE = re.compile(r"\d+(?:\.\d+){1,3}")

# 条文结构识别（行首正则）
_FRONT_MATTER_RE = re.compile(r"^(前言|目次|目录|Contents|目錄)\s*$")
_LEVEL1_RE = re.compile(r"^(\d+)\s+\S+")  # 一级标题：1 总则
_LEVEL2_RE = re.compile(r"^(\d+\.\d+)\s+\S+")  # 二级标题：1.1 一般规定
_CLAUSE_HEAD_RE = re.compile(r"^(\d+\.\d+\.\d+)(?![\d.\-])")  # 条文：1.1.1
_TABLE_NO_RE = re.compile(r"^表?\s*\d+\.\d+\.\d+-[A-Z]")  # 表格编号：表 1.1.1-A

# 二次切分的分隔符（优先按句子边界，避免切断句子）
_SEPARATORS = ["\n", "。", "；", "，", " ", ""]


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


def split_clauses(pages: list[dict], max_chars: int = 500) -> list[dict]:
    """语义条文切块：按「1.X.X 条文」切分，前言/目次跳过，标题只作元数据。

    输入 pages 为 [{"page": int, "text": str}, ...]（OCR 或文字层的每页文本），
    返回 chunk dict：content / chapter / section / clause / page / has_table。
    条文跨页记页码范围（如 "5-6"），超长条文（>max_chars）二次切分。
    """
    chunks: list[dict] = []
    chapter = ""
    section = ""
    clause = ""
    lines: list[str] = []
    page_nos: list[int] = []
    has_table = False
    skip = False  # 前言/目次/Contents 跳过态

    def flush() -> None:
        nonlocal clause, lines, page_nos, has_table
        if clause and lines:
            text = "\n".join(lines).strip()
            if text:
                chunks.extend(
                    _split_long(text, chapter, section, clause, page_nos, has_table, max_chars)
                )
        clause = ""
        lines = []
        page_nos = []
        has_table = False

    for p in pages:
        page_no = p["page"]
        text = p["text"]
        for raw in text.splitlines():
            line = raw.strip()
            if not line:
                continue

            if _FRONT_MATTER_RE.match(line):
                flush()
                skip = True
                continue

            if _CLAUSE_HEAD_RE.match(line):
                skip = False
                flush()
                clause = _CLAUSE_HEAD_RE.match(line).group(1)
                lines = [line]
                page_nos = [page_no]
                continue

            if _TABLE_NO_RE.match(line):
                skip = False
                if clause:
                    has_table = True
                    lines.append(line)
                    _add_page(page_nos, page_no)
                continue

            if _LEVEL2_RE.match(line):
                skip = False
                section = line
                flush()
                continue

            if _LEVEL1_RE.match(line):
                skip = False
                chapter = line
                flush()
                continue

            if not skip and clause:
                lines.append(line)
                _add_page(page_nos, page_no)

    flush()
    return chunks


def _split_long(
    text: str,
    chapter: str,
    section: str,
    clause: str,
    page_nos: list[int],
    has_table: bool,
    max_chars: int,
) -> list[dict]:
    """超长条文二次切分（overlap=0），子块共享章节/条款元数据。"""
    page = _page_range(page_nos)
    base = {
        "chapter": chapter,
        "section": section,
        "clause": clause,
        "page": page,
        "has_table": has_table,
    }
    if len(text) <= max_chars:
        return [{**base, "content": text}]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_chars, chunk_overlap=0, separators=_SEPARATORS
    )
    return [
        {**base, "content": part.strip()}
        for part in splitter.split_text(text)
        if part.strip()
    ]


def _add_page(page_nos: list[int], page_no: int) -> None:
    if page_no not in page_nos:
        page_nos.append(page_no)


def _page_range(page_nos: list[int]) -> str:
    """页码记范围：单页记 "5"，跨页记 "5-6"。"""
    if not page_nos:
        return ""
    pages = sorted(set(page_nos))
    if len(pages) == 1:
        return str(pages[0])
    return f"{pages[0]}-{pages[-1]}"
