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
        f"1. Try to use all of the provided words naturally and prefer the supplied meanings. "
        f"If one coherent article cannot use them well, split the output into 2 or more short bilingual articles so that as many words as possible are covered.\n"
        "2. Output in Markdown.\n"
        "3. For each article, start with a title and a one-line theme sentence in Chinese.\n"
        "4. For each article, write 3 to 4 English paragraphs totaling around 360 to 520 words.\n"
        "5. After each English paragraph, provide a fluent Chinese translation rather than a word-by-word translation.\n"
        "6. Keep each article coherent, specific, and readable, as if it were a short magazine passage.\n"
        "7. Do not force every word into one scene. If needed, distribute the words across multiple articles instead of dropping too many words.\n"
        "8. End with a short vocabulary recap table with columns: Word | Meaning. If there are multiple articles, provide one combined recap table at the end.\n"
        f"{missing_note}"
        "Vocabulary:\n"
        + "\n".join(vocabulary_lines)
    )
