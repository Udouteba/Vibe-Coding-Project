"""扫描件 OCR 与表格解析：无文字层 PDF 走 PaddleOCR / PP-Structure。

职责：PDF 渲染 RGB 图 → 浅灰水印白化 → 版面分析（文字/表格分流）
→ 表格转 Markdown + 列表重建 + 水印词过滤，返回每页「页码 + 文本」。

纯函数可独立测试；引擎懒加载单例，模式同 vector_store_service.get_embeddings。
"""

import logging
from collections.abc import Iterator
from dataclasses import dataclass
from html.parser import HTMLParser

import fitz  # pymupdf
import numpy as np
from PIL import Image

from config import settings

from ..utils.latex_clean import clean_inline_latex

logger = logging.getLogger("drainage")


@dataclass
class Block:
    """版面分析输出块：类型 + 边界框 + 内容。"""

    type: str  # text / title / table / figure / formula
    bbox: list[float]  # [x0, y0, x1, y1]
    content: str  # 文本、表格的 Markdown，或公式的 LaTeX


# ---------------------------------------------------------------------------
# 图片渲染与去水印
# ---------------------------------------------------------------------------

def iter_pdf_images(
    path: str,
    dpi: int | None = None,
    start_page: int = 1,
    page_count: int | None = None,
) -> Iterator[Image.Image]:
    """逐页渲染 PDF 为 RGB 图（生成器，边渲染边释放，避免长文档一次性占用全部内存）。

    start_page（1-based）/ page_count 用于分批：跳过前面页不渲染，节省时间。
    """
    dpi = dpi or settings.OCR_DPI
    max_side = settings.OCR_MAX_SIDE
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    doc = fitz.open(path)
    try:
        for idx, page in enumerate(doc, 1):
            if idx < start_page:
                continue
            if page_count is not None and idx >= start_page + page_count:
                break
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            yield _limit_size(img, max_side)
    finally:
        doc.close()


def pdf_to_images(path: str, dpi: int | None = None) -> list[Image.Image]:
    """PDF 每页渲染为 RGB 图列表（PIL 'RGB' 模式，供 PP-Structure 3 通道输入）。"""
    return list(iter_pdf_images(path, dpi))


def _limit_size(img: Image.Image, max_side: int) -> Image.Image:
    """最长边超过 max_side 时等比缩小，规避 paddle CPU 大图 segfault。"""
    if max(img.size) <= max_side:
        return img
    ratio = max_side / max(img.size)
    size = (round(img.width * ratio), round(img.height * ratio))
    return img.resize(size)


def remove_watermark(img: Image.Image, threshold: int | None = None) -> Image.Image:
    """浅灰白化：按灰度阈值把浅色水印置白，深色文字与表格线保留（非硬二值化）。"""
    threshold = threshold if threshold is not None else settings.OCR_WM_THRESHOLD
    rgb = img.convert("RGB")
    gray = rgb.convert("L")
    mask = gray.point(lambda p: 255 if p >= threshold else 0)
    white = Image.new("RGB", rgb.size, (255, 255, 255))
    return Image.composite(white, rgb, mask)


# ---------------------------------------------------------------------------
# 文本过滤
# ---------------------------------------------------------------------------

def _watermark_words() -> list[str]:
    return [w.strip() for w in settings.OCR_WM_WORDS.split(",") if w.strip()]


def filter_watermark_text(text: str) -> str:
    """剔除水印黑名单词；结果为空视为整块水印（调用方丢弃）。"""
    for w in _watermark_words():
        text = text.replace(w, "")
    return text.strip()


# ---------------------------------------------------------------------------
# 表格 HTML → Markdown
# ---------------------------------------------------------------------------

class _TableParser(HTMLParser):
    """解析 PP-Structure 输出的表格 HTML，提取含 colspan/rowspan 的单元格。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[dict]] = []
        self._row: list[dict] | None = None
        self._cell: dict | None = None
        self._in_cell = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th"):
            self._cell = {
                "text": "",
                "colspan": int(a.get("colspan", 1)),
                "rowspan": int(a.get("rowspan", 1)),
            }
            self._in_cell = True

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None:
            if self._row is not None:
                self._row.append(self._cell)
            self._cell = None
            self._in_cell = False
        elif tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None

    def handle_data(self, data):
        if self._in_cell and self._cell is not None:
            self._cell["text"] += data


def _expand_grid(rows: list[list[dict]]) -> tuple[list[list[str]], int]:
    """展开 colspan/rowspan 到等宽二维网格，返回 (grid, 列数)。"""
    grid: list[list[str]] = []
    occupied: set[tuple[int, int]] = set()
    for r, cells in enumerate(rows):
        while len(grid) <= r:
            grid.append([])
        c = 0
        for cell in cells:
            while (r, c) in occupied:
                c += 1
            for dc in range(cell["colspan"]):
                while len(grid[r]) <= c + dc:
                    grid[r].append("")
                grid[r][c + dc] = cell["text"] if dc == 0 else ""
            for dr in range(1, cell["rowspan"]):
                for dc in range(cell["colspan"]):
                    occupied.add((r + dr, c + dc))
            c += cell["colspan"]
    ncols = max((len(row) for row in grid), default=0)
    for row in grid:
        while len(row) < ncols:
            row.append("")
    return grid, ncols


def _cell_md(text: str) -> str:
    return text.replace("\n", "<br>").replace("|", "\\|")


def table_html_to_markdown(html: str) -> str:
    """表格 HTML（含 colspan/rowspan）→ Markdown 管道表。"""
    parser = _TableParser()
    parser.feed(html)
    parser.close()
    if not parser.rows:
        return html.strip()
    grid, ncols = _expand_grid(parser.rows)
    if ncols == 0:
        return ""
    lines = ["| " + " | ".join(_cell_md(c) for c in grid[0]) + " |"]
    lines.append("| " + " | ".join("---" for _ in range(ncols)) + " |")
    for row in grid[1:]:
        lines.append("| " + " | ".join(_cell_md(c) for c in row) + " |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 正文块重建
# ---------------------------------------------------------------------------

def reconstruct_list(blocks: list[Block]) -> str:
    """按版面阅读顺序（parse_page 已排序）拼接内容块，表格块输出 Markdown。"""
    parts = [b.content.strip() for b in blocks if b.content.strip()]
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# 引擎懒加载 + 版面分析 + 入口
# ---------------------------------------------------------------------------

_engine = None

# 跳过无文本价值的块：图片/图表/印章/页眉页脚/页码与公式编号等附属块
_SKIP_LABELS = {
    "image",
    "chart",
    "flowchart",
    "figure",
    "seal",
    "aside_text",
    "number",
    "formula_number",
    "header",
    "header_image",
    "footer",
    "footer_image",
    "footnote",
}

_TITLE_LABELS = {
    "paragraph_title",
    "doc_title",
    "abstract_title",
    "reference_title",
    "content_title",
    "title",
    "table_title",
    "chart_title",
    "figure_title",
    "figure_table_chart_title",
}


def _get_engine():
    """懒加载 PPStructureV3 单例（延迟 import paddle，避免启动即加载重依赖）。"""
    global _engine
    if _engine is None:
        from paddleocr import PPStructureV3

        logger.info("加载 PP-Structure 版面分析引擎（首次调用会下载模型）")
        _engine = PPStructureV3(
            lang="ch",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            use_seal_recognition=False,
            use_formula_recognition=True,
            use_chart_recognition=False,
            use_table_recognition=settings.OCR_USE_TABLE,
            enable_mkldnn=False,  # Windows CPU 下 paddle oneDNN PIR 回归，禁用规避
        )
    return _engine


def parse_page(img: Image.Image) -> list[Block]:
    """版面分析一页，返回按阅读顺序的内容块（图片/页眉/页码等已跳过）。"""
    engine = _get_engine()
    # 用 np.array（可写副本）而非 np.asarray：公式识别会原地改写图像（置白公式区），
    # np.asarray(PIL.Image) 返回只读数组会触发 "assignment destination is read-only"。
    result = engine.predict(np.array(img))
    blocks: list[Block] = []
    for page_res in result:
        for lb in page_res["parsing_res_list"]:
            label = lb.label
            if label in _SKIP_LABELS:
                continue
            content = (lb.content or "").strip()
            if not content:
                continue
            if label == "table":
                content = table_html_to_markdown(content)
                btype = "table"
            elif label == "formula":
                btype = "formula"
            elif label in _TITLE_LABELS:
                btype = "title"
            else:
                btype = "text"
            # 独立公式块保留 LaTeX，其余块清洗内联 $...$ 片段
            if btype != "formula":
                content = clean_inline_latex(content)
            blocks.append(Block(type=btype, bbox=list(lb.bbox), content=content))
    return blocks


def ocr_page(img: Image.Image) -> str:
    """单页 OCR：版面分析 → 正文重建 → 水印过滤，返回纯文本。"""
    blocks = parse_page(remove_watermark(img))
    return filter_watermark_text(reconstruct_list(blocks))


def extract_pdf_text(path: str) -> list[dict]:
    """扫描件入口：逐页 OCR，返回每页「页码 + 文本」（单进程整本，供旧调用/测试复用）。"""
    pages: list[dict] = []
    for page_no, img in enumerate(iter_pdf_images(path), 1):
        text = ocr_page(img)
        if text:
            pages.append({"page": page_no, "text": text})
    return pages
