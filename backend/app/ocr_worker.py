"""OCR 子进程入口：在主进程外独立加载 paddle，逐页 OCR 写 jsonl。

独立子进程隔离 paddle 与 torch（embedding），避免同进程 OpenMP 运行时冲突导致的段错误。
每页结果立即 append + flush 到输出文件，实现页级断点续传。
"""

import argparse
import json
import sys

from app.services import ocr_service


def _append_page(out: str, page_no: int, text: str) -> None:
    with open(out, "a", encoding="utf-8") as f:
        f.write(json.dumps({"page": page_no, "text": text}, ensure_ascii=False) + "\n")
        f.flush()


def main() -> int:
    parser = argparse.ArgumentParser(description="给排水智库 OCR worker")
    parser.add_argument("--pdf", required=True, help="PDF 文件路径")
    parser.add_argument("--out", required=True, help="jsonl 输出路径（追加写）")
    parser.add_argument("--start", type=int, default=1, help="起始页（1-based）")
    parser.add_argument("--count", type=int, required=True, help="本批处理页数")
    args = parser.parse_args()

    for page_no, img in enumerate(
        ocr_service.iter_pdf_images(args.pdf, start_page=args.start, page_count=args.count),
        args.start,
    ):
        text = ocr_service.ocr_page(img)
        if text:
            _append_page(args.out, page_no, text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
