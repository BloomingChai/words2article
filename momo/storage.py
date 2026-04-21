"""本地存储层。

这里负责把生成结果写到输出目录和缓存目录中，
包括文章正文、当天词表和提示词文本。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def article_path(output_dir: Path, article_date: str) -> Path:
    """计算当天文章的输出路径。"""
    return output_dir / f"{article_date}.md"


def cache_payload(path: Path, payload: Any) -> None:
    """把 JSON 数据写入缓存文件。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_cached_payload(path: Path) -> Any | None:
    """读取缓存 JSON；文件不存在时返回 None。"""
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_cached_text(path: Path) -> str | None:
    """读取缓存文本；文件不存在时返回 None。"""
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def write_article(path: Path, article: str) -> None:
    """把文章文本写到指定文件。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(article + "\n", encoding="utf-8")


def write_article_copies(paths: list[Path], article: str) -> None:
    """把同一篇文章写到多个目标路径。"""
    seen: set[Path] = set()
    for path in paths:
        if path in seen:
            continue
        write_article(path, article)
        seen.add(path)
