"""通用 HTTP 请求层。

这个模块把 JSON 请求、错误处理和响应解析统一封装起来，
其他模块只需要关心业务参数。
"""

from __future__ import annotations

import json
import socket
import time
from collections.abc import Iterator
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
    attempts = 3

    for attempt in range(1, attempts + 1):
        req = request.Request(url, data=body, method="POST")
        for key, value in headers.items():
            req.add_header(key, value)

        try:
            with request.urlopen(req, timeout=timeout) as response:
                raw = response.read().decode("utf-8", errors="replace")
                if not raw.strip():
                    raise SystemExit(f"Empty response calling {url}")
                try:
                    return json.loads(raw)
                except json.JSONDecodeError as exc:
                    snippet = raw[:300].strip()
                    raise SystemExit(
                        f"Non-JSON response calling {url}\n{snippet}"
                    ) from exc
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="ignore")
            raise SystemExit(f"HTTP {exc.code} calling {url}\n{details}") from exc
        except (TimeoutError, socket.timeout) as exc:
            if attempt == attempts:
                raise SystemExit(
                    f"Request timed out after {attempts} attempts calling {url}. "
                    f"Try again, or increase --timeout beyond {timeout} seconds."
                ) from exc
            time.sleep(attempt)
        except error.URLError as exc:
            if isinstance(exc.reason, TimeoutError | socket.timeout):
                if attempt == attempts:
                    raise SystemExit(
                        f"Request timed out after {attempts} attempts calling {url}. "
                        f"Try again, or increase --timeout beyond {timeout} seconds."
                    ) from exc
                time.sleep(attempt)
                continue
            raise SystemExit(f"Network error calling {url}: {exc}") from exc

    raise SystemExit(f"Request failed calling {url}")


def unwrap_api_data(response: dict[str, Any]) -> dict[str, Any]:
    """兼容部分接口外层包裹 data 字段的返回格式。"""
    data = response.get("data")
    if isinstance(data, dict):
        return data
    return response


def stream_json_events(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout: int,
) -> Iterator[dict[str, Any]]:
    """发送流式请求并按 OpenAI 兼容 SSE 事件产出 JSON 数据。"""
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=body, method="POST")
    for key, value in headers.items():
        req.add_header(key, value)

    try:
        with request.urlopen(req, timeout=timeout) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line or not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if not data or data == "[DONE]":
                    continue
                try:
                    yield json.loads(data)
                except json.JSONDecodeError as exc:
                    snippet = data[:300].strip()
                    raise SystemExit(
                        f"Non-JSON stream event calling {url}\n{snippet}"
                    ) from exc
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="ignore")
        raise SystemExit(f"HTTP {exc.code} calling {url}\n{details}") from exc
    except (TimeoutError, socket.timeout) as exc:
        raise SystemExit(
            f"Streaming request timed out calling {url}. "
            f"Try again, or increase --timeout beyond {timeout} seconds."
        ) from exc
    except error.URLError as exc:
        raise SystemExit(f"Network error calling {url}: {exc}") from exc
