from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from momo.http import post_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send a minimal test request to the configured LLM service."
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="HTTP timeout in seconds.",
    )
    parser.add_argument(
        "--prompt",
        default="Reply with exactly: OK",
        help="Prompt to send to the LLM.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    api_key = (os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
    llm_url = os.getenv("LLM_API_URL", "https://api.siliconflow.cn/v1/chat/completions").strip()
    model = os.getenv("LLM_MODEL", "Pro/deepseek-ai/DeepSeek-V3.2").strip()

    if not api_key:
        raise SystemExit("Missing required config: LLM_API_KEY or OPENAI_API_KEY")

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": "You are a concise assistant."},
            {"role": "user", "content": args.prompt},
        ],
    }

    response = post_json(llm_url, payload, headers, args.timeout)
    choices = response.get("choices") or []
    if not choices:
        raise SystemExit("LLM response did not contain choices")

    message = choices[0].get("message") or {}
    content = str(message.get("content") or "").strip()
    if not content:
        raise SystemExit("LLM response did not contain message content")

    print("LLM service is reachable.")
    print(f"Model: {model}")
    print("Response:")
    print(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
