"""主流程编排层。

这里负责把命令行参数、配置、墨墨数据接口、词书、提示词、
大模型生成和本地存储串成完整的一条执行链。
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

from .article import build_prompt
from .cli import parse_args
from .config import AppConfig, ensure_config_ready, load_config
from .llm import complete_missing_words_with_llm, generate_article
from .storage import (
    article_path,
    cache_payload,
    load_cached_payload,
    load_cached_text,
    write_article,
    write_article_copies,
)
from .study_api import diagnose_empty_today_items, fetch_today_items
from .words import enrich_words, filter_review_words, format_word_report, load_word_book


def prepare_words(args: argparse.Namespace, config: AppConfig) -> tuple[list[dict], list[dict]]:
    """把当天单词和本地词书整理成后续生成文章可用的数据。"""
    word_index = load_word_book(config.word_book_path)
    items = fetch_today_items(config)
    words = enrich_words(items, word_index)
    words = filter_review_words(words, include_well_familiar=args.include_well_familiar)
    words = complete_missing_words_with_llm(
        config,
        words,
        config.cache_dir / "word_supplements.json",
    )
    return items, words


def cache_word_data(config: AppConfig, article_date: str, items: list[dict], words: list[dict]) -> None:
    cache_payload(config.cache_dir / f"{article_date}-today-items.json", items)
    cache_payload(config.cache_dir / f"{article_date}-words.json", words)


def load_or_prepare_words(args: argparse.Namespace, config: AppConfig) -> tuple[list[dict], list[dict]] | None:
    items, words = prepare_words(args, config)
    if not words:
        sys.stdout.write(diagnose_empty_today_items(config) + "\n")
        return None
    cache_word_data(config, args.date, items, words)
    return items, words


def run_today(args: argparse.Namespace, config: AppConfig) -> int:
    """生成或展示当天文章。"""
    output_path = article_path(config.output_dir, args.date)
    if output_path.exists() and not args.force:
        sys.stdout.write(output_path.read_text(encoding="utf-8"))
        return 0

    prepared = load_or_prepare_words(args, config)
    if prepared is None:
        return 0
    items, words = prepared

    prompt = build_prompt(words, args.date)
    article = generate_article(config, prompt)

    write_article(config.cache_dir / f"{args.date}-prompt.txt", prompt)

    if not args.stdout_only:
        write_article_copies(
            [
                output_path,
                article_path(config.obsidian_output_dir, args.date),
            ],
            article,
        )
    return 0


def load_cached_words(config: AppConfig, article_date: str) -> list[dict[str, Any]]:
    words = load_cached_payload(config.cache_dir / f"{article_date}-words.json")
    if not isinstance(words, list):
        raise SystemExit(
            "Missing cached words for regenerate.\n"
            "Run './run.sh words' or './run.sh generate --force' first."
        )
    return words


def load_cached_prompt_or_build(
    config: AppConfig,
    article_date: str,
    words: list[dict[str, Any]],
) -> str:
    prompt_path = config.cache_dir / f"{article_date}-prompt.txt"
    prompt = load_cached_text(prompt_path)
    if prompt is not None:
        return prompt
    prompt = build_prompt(words, article_date)
    write_article(prompt_path, prompt)
    return prompt


def run_regenerate(args: argparse.Namespace, config: AppConfig) -> int:
    """只基于缓存重生成文章，不重新拉取当天单词。"""
    words = load_cached_words(config, args.date)
    prompt = load_cached_prompt_or_build(config, args.date, words)
    article = generate_article(config, prompt)

    if not args.stdout_only:
        write_article_copies(
            [
                article_path(config.output_dir, args.date),
                article_path(config.obsidian_output_dir, args.date),
            ],
            article,
        )
    return 0


def run_words(args: argparse.Namespace, config: AppConfig) -> int:
    """只输出当天单词列表，不生成文章。"""
    prepared = load_or_prepare_words(args, config)
    if prepared is None:
        return 0
    _, words = prepared
    sys.stdout.write(format_word_report(words) + "\n")
    return 0


def main() -> int:
    """程序主入口。"""
    args = parse_args()
    config = load_config(args)
    ensure_config_ready(config, args.command)

    if args.command == "words":
        return run_words(args, config)
    if args.command == "regenerate":
        return run_regenerate(args, config)
    return run_today(args, config)
