"""
Data source abstraction for the MCP server.

Provides a uniform interface for reading parsed application data
from either local filesystem or a GitHub repository.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError


class DataSource(ABC):
    """Abstract interface for reading parsed application data."""

    @abstractmethod
    def list_apps(self) -> list[str]:
        """Return folder names of available applications."""

    @abstractmethod
    def read_json(self, app_name: str, rel_path: str) -> dict | list:
        """Read and parse a JSON file. Raises FileNotFoundError if missing."""

    @abstractmethod
    def file_exists(self, app_name: str, rel_path: str) -> bool:
        """Check if a file exists."""


class LocalDataSource(DataSource):
    """Reads data from a local directory."""

    def __init__(self, data_dir: str):
        self._root = Path(data_dir)
        if not self._root.is_dir():
            raise FileNotFoundError(f"Data directory not found: {self._root}")

    def list_apps(self) -> list[str]:
        return sorted(
            e.name for e in self._root.iterdir()
            if e.is_dir() and (e / "manifest.json").exists()
        )

    def read_json(self, app_name: str, rel_path: str) -> dict | list:
        path = self._root / app_name / rel_path
        if not path.exists():
            raise FileNotFoundError(f"Not found: {app_name}/{rel_path}")
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def file_exists(self, app_name: str, rel_path: str) -> bool:
        return (self._root / app_name / rel_path).exists()


class GitHubDataSource(DataSource):
    """Reads data from a GitHub repository via raw content URLs.

    Uses in-memory caching to avoid repeated fetches for the same file.
    """

    def __init__(self, owner: str, repo: str, branch: str = "main",
                 token: str | None = None, data_prefix: str = "data"):
        self._owner = owner
        self._repo = repo
        self._branch = branch
        self._token = token or os.environ.get("GITHUB_TOKEN", "")
        self._prefix = data_prefix
        self._cache: dict[str, dict | list] = {}
        self._app_list: list[str] | None = None

    def _raw_url(self, path: str) -> str:
        return f"https://raw.githubusercontent.com/{self._owner}/{self._repo}/{self._branch}/{path}"

    def _api_url(self, path: str) -> str:
        return f"https://api.github.com/repos/{self._owner}/{self._repo}/contents/{path}?ref={self._branch}"

    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {"Accept": "application/vnd.github.v3+json"}
        if self._token:
            h["Authorization"] = f"token {self._token}"
        return h

    def _fetch_raw(self, path: str) -> bytes:
        """Fetch raw file content from GitHub."""
        url = self._raw_url(path)
        req = Request(url, headers=self._headers())
        try:
            with urlopen(req, timeout=30) as resp:
                return resp.read()
        except HTTPError as e:
            if e.code == 404:
                raise FileNotFoundError(f"Not found on GitHub: {path}")
            raise

    def _fetch_json(self, path: str) -> dict | list:
        """Fetch and parse a JSON file, with caching."""
        if path in self._cache:
            return self._cache[path]
        data = json.loads(self._fetch_raw(path))
        self._cache[path] = data
        return data

    def _list_directory(self, path: str) -> list[dict]:
        """List directory contents via GitHub Contents API."""
        url = self._api_url(path)
        req = Request(url, headers=self._headers())
        try:
            with urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except HTTPError as e:
            if e.code == 404:
                return []
            raise

    def list_apps(self) -> list[str]:
        if self._app_list is not None:
            return self._app_list
        entries = self._list_directory(self._prefix)
        self._app_list = sorted(
            e["name"] for e in entries
            if e.get("type") == "dir"
        )
        return self._app_list

    def read_json(self, app_name: str, rel_path: str) -> dict | list:
        full_path = f"{self._prefix}/{app_name}/{rel_path}"
        return self._fetch_json(full_path)

    def file_exists(self, app_name: str, rel_path: str) -> bool:
        full_path = f"{self._prefix}/{app_name}/{rel_path}"
        if full_path in self._cache:
            return True
        try:
            self._fetch_json(full_path)
            return True
        except FileNotFoundError:
            return False
