"""词书处理层。"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def normalize_word(word: str) -> str:
    """把单词做统一归一化，方便匹配。"""
    cleaned = word.strip().lower()
    cleaned = re.sub(r"^[^a-z0-9]+|[^a-z0-9]+$", "", cleaned)
    return " ".join(cleaned.split())


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


def normalize_examples(examples: Any) -> list[dict[str, str]]:
    normalized = []
    if not isinstance(examples, list):
        return normalized

    for entry in examples[:3]:
        if not isinstance(entry, dict):
            continue
        phrase = str(entry.get("en", "")).strip()
        translation = str(entry.get("zh", "")).strip()
        if not phrase or not translation:
            continue
        normalized.append({"phrase": phrase, "translation": translation})
    return normalized


def normalize_word_entry(item: dict[str, Any]) -> dict[str, Any]:
    """兼容旧词库和新的 Momo words 词库结构。"""
    translations = []
    raw_translations = item.get("translations")
    if isinstance(raw_translations, list):
        translations = [
            {
                "type": str(entry.get("type", "")).strip(),
                "translation": str(entry.get("translation", "")).strip(),
            }
            for entry in raw_translations
            if isinstance(entry, dict) and str(entry.get("translation", "")).strip()
        ]
    else:
        raw_definitions = item.get("definitions")
        if isinstance(raw_definitions, list):
            for definition in raw_definitions:
                translations.extend(split_definition_text(str(definition)))

    raw_phrases = item.get("phrases")
    if isinstance(raw_phrases, list):
        phrases = [
            {
                "phrase": str(entry.get("phrase", "")).strip(),
                "translation": str(entry.get("translation", "")).strip(),
            }
            for entry in raw_phrases[:3]
            if isinstance(entry, dict) and str(entry.get("phrase", "")).strip()
        ]
    else:
        phrases = normalize_examples(item.get("examples"))

    return {
        "word": str(item.get("word", "")).strip(),
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
        normalized = normalize_word(word)
        word_entry = word_index.get(normalized)

        translations = []
        phrases = []
        if word_entry:
            translations = word_entry.get("translations", []) or []
            phrases = word_entry.get("phrases", []) or []

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
                "translations": [
                    {
                        "type": entry.get("type", ""),
                        "translation": str(entry.get("translation", "")).strip(),
                    }
                    for entry in translations
                    if isinstance(entry, dict) and str(entry.get("translation", "")).strip()
                ],
                "phrases": [
                    {
                        "phrase": str(entry.get("phrase", "")).strip(),
                        "translation": str(entry.get("translation", "")).strip(),
                    }
                    for entry in phrases[:3]
                    if isinstance(entry, dict) and str(entry.get("phrase", "")).strip()
                ],
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
