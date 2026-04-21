"""文章提示词构建层。

这里把当天词汇整理成适合大模型写双语短文的提示词。
"""

from __future__ import annotations

from typing import Any


def build_prompt(words: list[dict[str, Any]], article_date: str) -> str:
    """根据当天单词和日期拼出生成文章所需的提示词。"""
    vocabulary_lines = []
    missing = []
    target_count = max(len(words), 1)
    lower_bound = max(1, target_count - 1)

    for item in words:
        if item["translations"]:
            translation_text = "; ".join(
                f"{entry['type'] or 'unknown'} {entry['translation']}"
                for entry in item["translations"][:3]
            )
            phrase_text = ""
            if item["phrases"]:
                phrase_pairs = [
                    f"{entry['phrase']} ({entry['translation']})" for entry in item["phrases"]
                ]
                phrase_text = " | phrases: " + "; ".join(phrase_pairs)
            source_note = ""
            if item.get("source") == "llm_supplement":
                source_note = " | note: supplemented meaning"
            vocabulary_lines.append(
                f"- {item['word']}: {translation_text}{phrase_text}{source_note}"
            )
        else:
            missing.append(item["word"])
            vocabulary_lines.append(f"- {item['word']}: meaning not found in local word book")

    missing_note = ""
    if missing:
        missing_note = (
            "If a word lacks a local meaning, use it conservatively and keep the context simple.\n"
        )

    return (
        f"Today is {article_date}.\n"
        "Write a polished bilingual reading passage for an English learner.\n"
        "Requirements:\n"
        f"1. Use {lower_bound} to {target_count} of the provided words naturally. Prefer the supplied meanings.\n"
        "2. Output in Markdown.\n"
        "3. Start with a title and a one-line theme sentence in Chinese.\n"
        "4. Write 3 to 4 English paragraphs totaling around 360 to 520 words.\n"
        "5. After each English paragraph, provide a fluent Chinese translation rather than a word-by-word translation.\n"
        "6. Keep the article coherent, specific, and readable, as if it were a short magazine passage.\n"
        "7. Do not force every word into one scene. It is acceptable to leave a few unused if that improves quality.\n"
        "8. End with a short vocabulary recap table with columns: Word | Meaning | How it was used.\n"
        f"{missing_note}"
        "Vocabulary:\n"
        + "\n".join(vocabulary_lines)
    )
