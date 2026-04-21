"""大模型调用层。

这里负责两件事：补全词书里缺失的词义，以及生成最终的双语文章。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import AppConfig
from .http import post_json, unwrap_api_data
from .words import normalize_word


def load_word_supplements(path: Path) -> dict[str, dict[str, Any]]:
    """读取本地保存的补词缓存。"""
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    return {normalize_word(key): value for key, value in data.items() if isinstance(value, dict)}


def save_word_supplements(path: Path, data: dict[str, dict[str, Any]]) -> None:
    """保存补词缓存到本地。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = dict(sorted(data.items(), key=lambda item: item[0]))
    path.write_text(json.dumps(ordered, ensure_ascii=False, indent=2), encoding="utf-8")


def request_word_supplements(config: AppConfig, words: list[str]) -> list[dict[str, Any]]:
    """让大模型为缺失单词生成简短词义补充。"""
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {config.llm_api_key}",
        "Content-Type": "application/json",
    }
    prompt = (
        "You are filling missing bilingual glossary entries for English learners.\n"
        "Return JSON only. No markdown.\n"
        "Schema: {\"items\":[{\"word\":\"...\",\"translations\":[{\"type\":\"adv\",\"translation\":\"...\"}]}]}\n"
        "Rules:\n"
        "- Keep each Chinese meaning short and common.\n"
        "- Provide 1 to 3 likely meanings.\n"
        "- Use part-of-speech tags like n, v, adj, adv, prep, conj.\n"
        "- Do not invent phrases.\n"
        f"Words: {json.dumps(words, ensure_ascii=False)}"
    )
    payload = {
        "model": config.llm_model,
        "stream": False,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": "You output strict JSON only."},
            {"role": "user", "content": prompt},
        ],
    }
    response = unwrap_api_data(post_json(config.llm_url, payload, headers, config.timeout))
    choices = response.get("choices") or []
    if not choices:
        return []
    message = choices[0].get("message") or {}
    content = message.get("content")
    if not content:
        return []

    try:
        parsed = json.loads(str(content))
    except json.JSONDecodeError:
        return []
    items = parsed.get("items") or []
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def complete_missing_words_with_llm(
    config: AppConfig,
    words: list[dict[str, Any]],
    supplement_path: Path,
) -> list[dict[str, Any]]:
    """用本地缓存和大模型补全词书里缺失的词义。"""
    if not config.llm_api_key:
        return words

    supplements = load_word_supplements(supplement_path)
    missing = [item["word"] for item in words if not item["translations"]]
    unresolved = [word for word in missing if normalize_word(word) not in supplements]

    if unresolved:
        generated = request_word_supplements(config, unresolved)
        for entry in generated:
            word = str(entry.get("word", "")).strip()
            normalized = normalize_word(word)
            translations = entry.get("translations") or []
            if not normalized or not isinstance(translations, list):
                continue
            cleaned_translations = [
                {
                    "type": str(item.get("type", "")).strip(),
                    "translation": str(item.get("translation", "")).strip(),
                }
                for item in translations
                if isinstance(item, dict) and str(item.get("translation", "")).strip()
            ]
            if not cleaned_translations:
                continue
            supplements[normalized] = {
                "word": word,
                "translations": cleaned_translations[:3],
                "phrases": [],
                "source": "llm_supplement",
            }
        save_word_supplements(supplement_path, supplements)

    enriched = []
    for item in words:
        if item["translations"]:
            enriched.append(item)
            continue
        supplement = supplements.get(normalize_word(item["word"]))
        if not supplement:
            enriched.append(item)
            continue
        updated = dict(item)
        updated["matched"] = True
        updated["translations"] = supplement.get("translations", []) or []
        updated["phrases"] = supplement.get("phrases", []) or []
        updated["source"] = supplement.get("source", "llm_supplement")
        enriched.append(updated)
    return enriched


def generate_article(config: AppConfig, prompt: str) -> str:
    """调用大模型生成最终文章正文。"""
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {config.llm_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.llm_model,
        "stream": False,
        "messages": [
            {
                "role": "system",
                "content": "You are a careful bilingual English-writing assistant.",
            },
            {"role": "user", "content": prompt},
        ],
    }
    response = post_json(config.llm_url, payload, headers, config.timeout)
    choices = response.get("choices") or []
    if not choices:
        raise SystemExit("LLM response did not contain choices")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if not content:
        raise SystemExit("LLM response did not contain message content")
    return str(content).strip()
