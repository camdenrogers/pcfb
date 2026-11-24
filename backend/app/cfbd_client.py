"""Minimal client for the CollegeFootballData.com API (https://collegefootballdata.com).

Get a free API key at https://collegefootballdata.com/key. A full refresh of
one season costs 4 calls (teams, regular games, postseason games, talent).
"""
from __future__ import annotations

import time
from typing import Any

import httpx

from .config import settings


class CFBDError(RuntimeError):
    pass


class CFBDClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None, timeout: float = 30.0):
        key = api_key or settings.cfbd_api_key
        if not key:
            raise CFBDError("CFBD_API_KEY is not set. Get a free key at https://collegefootballdata.com/key")
        self._client = httpx.Client(
            base_url=base_url or settings.cfbd_base_url,
            headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
            timeout=timeout,
        )

    def __enter__(self) -> "CFBDClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def _get(self, path: str, **params: Any) -> list[dict]:
        params = {k: v for k, v in params.items() if v is not None}
        last: httpx.Response | None = None
        for attempt in range(4):
            resp = self._client.get(path, params=params)
            if resp.status_code in (429, 500, 502, 503, 504):
                last = resp
                time.sleep(2**attempt)
                continue
            if resp.status_code == 401:
                raise CFBDError("CFBD rejected the API key (401). Check CFBD_API_KEY.")
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else [data]
        raise CFBDError(f"CFBD request {path} failed after retries (HTTP {last.status_code if last else '?'})")

    def fbs_teams(self, year: int) -> list[dict]:
        return self._get("/teams/fbs", year=year)

    def games(self, year: int, season_type: str = "regular") -> list[dict]:
        return self._get("/games", year=year, seasonType=season_type)

    def talent(self, year: int) -> list[dict]:
        return self._get("/talent", year=year)
