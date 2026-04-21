"""主流程编排层。

这里负责把命令行参数、配置、墨墨数据接口、词书、提示词、
大模型生成和本地存储串成完整的一条执行链。
"""

from __future__ import annotations

import argparse
import sys

from .article import build_prompt
from .cli import parse_args
from .config import AppConfig, ensure_config_ready, load_config
from .llm import complete_missing_words_with_llm, generate_article
from .storage import article_path, build_front_matter, cache_payload, write_article
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


def run_today(args: argparse.Namespace, config: AppConfig) -> int:
    """生成或展示当天文章。"""
    output_path = article_path(config.output_dir, args.date)
    if output_path.exists() and not args.force:
        sys.stdout.write(output_path.read_text(encoding="utf-8"))
        return 0

    items, words = prepare_words(args, config)
    if not words:
        sys.stdout.write(diagnose_empty_today_items(config) + "\n")
        return 0

    prompt = build_prompt(words, args.date)
    article = generate_article(config, prompt)
    article = build_front_matter(words, args.date) + article

    cache_payload(config.cache_dir / f"{args.date}-today-items.json", items)
    cache_payload(config.cache_dir / f"{args.date}-words.json", words)
    write_article(config.cache_dir / f"{args.date}-prompt.txt", prompt)

    if not args.stdout_only:
        write_article(output_path, article)

    sys.stdout.write(article + ("\n" if not article.endswith("\n") else ""))
    return 0


def run_words(args: argparse.Namespace, config: AppConfig) -> int:
    """只输出当天单词列表，不生成文章。"""
    items, words = prepare_words(args, config)
    if not words:
        sys.stdout.write(diagnose_empty_today_items(config) + "\n")
        return 0
    cache_payload(config.cache_dir / f"{args.date}-today-items.json", items)
    cache_payload(config.cache_dir / f"{args.date}-words.json", words)
    sys.stdout.write(format_word_report(words) + "\n")
    return 0


def main() -> int:
    """程序主入口。"""
    args = parse_args()
    config = load_config(args)
    ensure_config_ready(config, args.command)

    if args.command == "words":
        return run_words(args, config)
    return run_today(args, config)
