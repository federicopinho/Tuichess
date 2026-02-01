from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = "https://lichess.org"


@dataclass
class ApiResult:
    ok: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class LichessClient:
    def __init__(self, token: Optional[str]) -> None:
        self._token = token

    def _request(self, path: str) -> ApiResult:
        headers = {"Accept": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        request = Request(f"{BASE_URL}{path}", headers=headers)
        try:
            with urlopen(request, timeout=10) as response:
                payload = response.read().decode("utf-8")
                data = json.loads(payload) if payload else {}
                return ApiResult(ok=True, data=data)
        except HTTPError as exc:
            return ApiResult(ok=False, error=f"HTTP {exc.code}: {exc.reason}")
        except URLError as exc:
            return ApiResult(ok=False, error=f"Network error: {exc.reason}")
        except json.JSONDecodeError:
            return ApiResult(ok=False, error="Invalid JSON response")

    def get_account(self) -> ApiResult:
        return self._request("/api/account")

    def get_now_playing(self) -> ApiResult:
        return self._request("/api/account/playing")
