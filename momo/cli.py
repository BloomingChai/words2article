"""命令行参数解析层。

这个模块只负责定义用户能在命令行上输入哪些命令和选项。
"""

from __future__ import annotations

import argparse
from datetime import date

from .config import DEFAULT_CACHE_DIR, DEFAULT_OUTPUT_DIR, DEFAULT_WORD_BOOK


def parse_args() -> argparse.Namespace:
    """解析命令行参数并返回结果。"""
    parser = argparse.ArgumentParser(
        description="Show or generate today's bilingual article from Momo words."
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="today",
        choices=["today", "generate", "regenerate", "words"],
        help="today/show today's article, generate a fresh one, regenerate from cache, or only list today's words",
    )
    parser.add_argument("--date", default=date.today().isoformat(), help="Date in YYYY-MM-DD")
    parser.add_argument("--limit", type=int, default=1000, help="Max words requested from Momo")
    parser.add_argument(
        "--include-well-familiar",
        action="store_true",
        help="Include words whose first response was WELL_FAMILIAR",
    )
    parser.add_argument(
        "--word-book",
        default=DEFAULT_WORD_BOOK,
        help="Path to the local JSON word book",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for generated markdown articles",
    )
    parser.add_argument(
        "--cache-dir",
        default=DEFAULT_CACHE_DIR,
        help="Directory for cached API payloads and prompts",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate today's article even if it already exists",
    )
    parser.add_argument(
        "--stdout-only",
        action="store_true",
        help="Print article without writing output files",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="HTTP timeout in seconds for both API calls",
    )
    return parser.parse_args()
