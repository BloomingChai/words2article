"""通用 HTTP 请求层。

这个模块把 JSON 请求、错误处理和响应解析统一封装起来，
其他模块只需要关心业务参数。
"""

from __future__ import annotations

import json
from typing import Any
from urllib import error, request


def post_json(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout: int,
) -> dict[str, Any]:
    """向指定地址发送 JSON POST 请求并返回解析后的结果。"""
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=body, method="POST")
    for key, value in headers.items():
        req.add_header(key, value)

    try:
        with request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="ignore")
        raise SystemExit(f"HTTP {exc.code} calling {url}\n{details}") from exc
    except error.URLError as exc:
        raise SystemExit(f"Network error calling {url}: {exc}") from exc


def unwrap_api_data(response: dict[str, Any]) -> dict[str, Any]:
    """兼容部分接口外层包裹 data 字段的返回格式。"""
    data = response.get("data")
    if isinstance(data, dict):
        return data
    return response
