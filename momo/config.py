"""配置读取和校验层。"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_WORD_BOOK = "momowords.core.json"
DEFAULT_OUTPUT_DIR = "output"
DEFAULT_OBSIDIAN_OUTPUT_DIR = "/Users/chai/Documents/Obsidian Vault/words2article"
DEFAULT_CACHE_DIR = "cache"
DEFAULT_MOMO_URL = "https://open.maimemo.com/open/api/v1/study/get_today_items"
DEFAULT_LLM_URL = "https://api.siliconflow.cn/v1/chat/completions"
DEFAULT_MODEL = "Pro/deepseek-ai/DeepSeek-V3.2"


@dataclass
class AppConfig:
    momo_token: str
    momo_url: str
    llm_api_key: str
    llm_url: str
    llm_model: str
    word_book_path: Path
    output_dir: Path
    obsidian_output_dir: Path
    cache_dir: Path
    request_limit: int
    timeout: int


def load_config(args: argparse.Namespace) -> AppConfig:
    """把命令行参数和环境变量合并成运行配置。"""
    momo_token = os.getenv("MOMO_API_TOKEN", "").strip()
    llm_api_key = (os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()

    return AppConfig(
        momo_token=momo_token,
        momo_url=os.getenv("MOMO_API_URL", DEFAULT_MOMO_URL).strip(),
        llm_api_key=llm_api_key,
        llm_url=os.getenv("LLM_API_URL", DEFAULT_LLM_URL).strip(),
        llm_model=os.getenv("LLM_MODEL", DEFAULT_MODEL).strip(),
        word_book_path=Path(args.word_book),
        output_dir=Path(args.output_dir),
        obsidian_output_dir=Path(
            os.getenv("OBSIDIAN_OUTPUT_DIR", DEFAULT_OBSIDIAN_OUTPUT_DIR).strip()
        ),
        cache_dir=Path(args.cache_dir),
        request_limit=args.limit,
        timeout=args.timeout,
    )


def ensure_config_ready(config: AppConfig, command: str) -> None:
    """检查启动所需配置是否完整。"""
    missing = []
    if not config.momo_token:
        missing.append("MOMO_API_TOKEN")
    if command != "words" and not config.llm_api_key:
        missing.append("LLM_API_KEY or OPENAI_API_KEY")
    if command != "regenerate" and not config.word_book_path.exists():
        missing.append(str(config.word_book_path))
    if missing:
        raise SystemExit("Missing required config: " + ", ".join(missing))
