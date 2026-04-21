"""本地存储层。

这里负责把生成结果写到输出目录和缓存目录中，
包括文章正文、当天词表和提示词文本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def article_path(output_dir: Path, article_date: str) -> Path:
    """计算当天文章的输出路径。"""
    return output_dir / f"{article_date}.md"


def cache_payload(path: Path, payload: Any) -> None:
    """把 JSON 数据写入缓存文件。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_article(path: Path, article: str) -> None:
    """把文章文本写到指定文件。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(article + "\n", encoding="utf-8")


def build_front_matter(words: list[dict[str, Any]], article_date: str) -> str:
    """为文章生成简单的头部注释信息。"""
    used_words = ", ".join(item["word"] for item in words[:12])
    return (
        f"<!-- generated_at: {datetime.now().isoformat(timespec='seconds')} -->\n"
        f"<!-- article_date: {article_date} -->\n"
        f"<!-- source_words: {used_words} -->\n\n"
    )
