"""词书处理层。"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


LEADING_INDEX_PATTERN = re.compile(r"^\s*(\d+)\s+(.+?)\s*$")


def normalize_word(word: str) -> str:
    """把单词做统一归一化，方便匹配。"""
    cleaned = word.strip().lower()
    cleaned = re.sub(r"^[^a-z0-9]+|[^a-z0-9]+$", "", cleaned)
    return " ".join(cleaned.split())


def clean_word_text(word: str) -> str:
    """清理词库中被索引号污染的 word 字段。"""
    cleaned = word.strip()
    match = LEADING_INDEX_PATTERN.match(cleaned)
    if match:
        return match.group(2).strip()
    return cleaned


def split_definition_text(text: str) -> list[dict[str, str]]:
    """把 `n. xxx；v. yyy` 这类释义拆成统一的内部结构。"""
    cleaned = " ".join(str(text).replace("\n", " ").split()).strip("；; ")
    if not cleaned:
        return []

    match = re.match(r"^([a-zA-Z.]+)\s+(.*)$", cleaned)
    if match:
        part_of_speech = match.group(1).rstrip(".").lower()
        body = match.group(2).strip("；; ")
    else:
        part_of_speech = ""
        body = cleaned

    pieces = [piece.strip() for piece in re.split(r"[；;]", body) if piece.strip()]
    if not pieces:
        return []
    return [{"type": part_of_speech, "translation": piece} for piece in pieces]


def is_usable_example(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False

    phrase = str(entry.get("en", "")).strip()
    translation = str(entry.get("zh", "")).strip()
    if len(phrase) < 3 or len(translation) < 2:
        return False
    if not re.search(r"[A-Za-z]", phrase):
        return False
    if phrase in {"/", "-"} or translation in {"/", "-"}:
        return False
    return True


def normalize_word_entry(item: dict[str, Any]) -> dict[str, Any]:
    """把 Momo words 词库条目转成项目内部使用的统一结构。"""
    translations = []
    for definition in item.get("definitions", []):
        translations.extend(split_definition_text(str(definition)))

    phrases = []
    for entry in item.get("examples", [])[:3]:
        if not is_usable_example(entry):
            continue
        phrase = str(entry.get("en", "")).strip()
        translation = str(entry.get("zh", "")).strip()
        phrases.append({"phrase": phrase, "translation": translation})

    return {
        "word": clean_word_text(str(item.get("word", ""))),
        "translations": translations[:6],
        "phrases": phrases,
    }


def load_word_book(path: Path) -> dict[str, dict[str, Any]]:
    """读取本地词书并建立单词索引。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit(f"Word book must be a JSON list: {path}")

    index: dict[str, dict[str, Any]] = {}
    for item in data:
        if not isinstance(item, dict):
            continue
        normalized_item = normalize_word_entry(item)
        word = normalized_item["word"]
        if not word:
            continue
        index[normalize_word(word)] = normalized_item
    return index


def enrich_words(
    items: list[dict[str, Any]],
    word_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """把墨墨单词和本地词书释义合并到一起。"""
    enriched = []
    for item in sorted(items, key=lambda value: value.get("order", 0)):
        word = str(item.get("voc_spelling", "")).strip()
        word_entry = word_index.get(normalize_word(word))

        enriched.append(
            {
                "word": word,
                "voc_id": item.get("voc_id"),
                "order": item.get("order"),
                "first_response": item.get("first_response"),
                "is_new": item.get("is_new"),
                "is_finished": item.get("is_finished"),
                "matched": bool(word_entry),
                "source": "word_book" if word_entry else "unmatched",
                "translations": word_entry.get("translations", []) if word_entry else [],
                "phrases": word_entry.get("phrases", []) if word_entry else [],
            }
        )
    return enriched


def filter_review_words(
    words: list[dict[str, Any]],
    include_well_familiar: bool = False,
) -> list[dict[str, Any]]:
    """过滤掉默认不想展示的熟词。"""
    if include_well_familiar:
        return words
    return [
        item
        for item in words
        if item.get("first_response") not in {"WELL_FAMILIAR"}
    ]


def format_word_report(words: list[dict[str, Any]]) -> str:
    """把当天单词整理成便于直接查看的文本报告。"""
    lines = ["Today's new words:"]
    for item in words:
        meaning = " / ".join(entry["translation"] for entry in item["translations"][:2]) or "N/A"
        lines.append(f"{item['order']:>2}. {item['word']} -> {meaning}")
    return "\n".join(lines)
