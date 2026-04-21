"""墨墨背单词接口层。

这里专门处理当天学习单词的获取，以及接口返回为空时的诊断信息。
"""

from __future__ import annotations

from typing import Any

from .config import AppConfig
from .http import post_json, unwrap_api_data


def fetch_today_items(config: AppConfig) -> list[dict[str, Any]]:
    """获取当天的新学单词。"""
    return fetch_today_items_with_filters(config, is_new=True)


def fetch_today_items_with_filters(
    config: AppConfig,
    is_new: bool | None = None,
    is_finished: bool | None = None,
) -> list[dict[str, Any]]:
    """按条件获取当天单词，用于不同的诊断场景。"""
    payload = {
        "limit": config.request_limit,
    }
    if is_new is not None:
        payload["is_new"] = is_new
    if is_finished is not None:
        payload["is_finished"] = is_finished
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {config.momo_token}",
        "Content-Type": "application/json",
    }
    response = unwrap_api_data(post_json(config.momo_url, payload, headers, config.timeout))
    items = response.get("today_items", [])
    if not isinstance(items, list):
        raise SystemExit("Unexpected Momo API response: today_items is not a list")
    return items


def diagnose_empty_today_items(config: AppConfig) -> str:
    """在当天单词为空时，尝试从不同筛选条件下给出诊断信息。"""
    variants = [
        ("new_words", {"is_new": True}),
        ("all_today_items", {}),
        ("non_new_today_items", {"is_new": False}),
        ("finished_today_items", {"is_finished": True}),
        ("unfinished_today_items", {"is_finished": False}),
    ]

    counts: list[str] = []
    for label, filters in variants:
        items = fetch_today_items_with_filters(
            config,
            is_new=filters.get("is_new"),
            is_finished=filters.get("is_finished"),
        )
        counts.append(f"{label}={len(items)}")

    return (
        "墨墨接口当前返回空列表。诊断结果："
        + ", ".join(counts)
        + "。这通常意味着 App 还没有把今天学习记录同步到开放接口，或者当前 token 对应的账号不是你刚刚学习的账号。"
    )
