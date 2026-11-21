"""Jira adapters.

local  - reads and writes JSON files in a folder (default: jira/). Used for demos
         and for teams without Jira access. Same shape the cloud adapter returns.
cloud  - Jira Cloud / Data Center REST API v2 over urllib (no third-party packages).
         Credentials come from environment variables, never from the config file.
"""
from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

from .util import VerifyError, expand_env, now_iso, read_json, write_json


class LocalJira:
    def __init__(self, folder: Path):
        self.folder = folder

    def _path(self, key: str) -> Path:
        if not re.fullmatch(r"[A-Z][A-Z0-9]+-\d+", key):
            raise VerifyError(f"'{key}' is not a Jira key like SHOP-142.")
        return self.folder / f"{key}.json"

    def get_issue(self, key: str) -> dict:
        p = self._path(key)
        if not p.is_file():
            raise VerifyError(f"No simulated Jira story at {p}.")
        return read_json(p)

    def add_comment(self, key: str, author: str, body: str) -> dict:
        issue = self.get_issue(key)
        comment = {"author": author, "created": now_iso(), "body": body}
        issue.setdefault("comments", []).append(comment)
        write_json(self._path(key), issue)
        return comment

    def transition(self, key: str, status: str) -> None:
        issue = self.get_issue(key)
        issue["status"] = status
        write_json(self._path(key), issue)


class CloudJira:
    def __init__(self, base_url: str, email: str, token: str, ac_field: str | None):
        if not (base_url and email and token):
            raise VerifyError(
                "Jira cloud adapter needs JIRA_BASE_URL, JIRA_EMAIL and JIRA_API_TOKEN in the environment."
            )
        self.base = base_url.rstrip("/")
        self.auth = "Basic " + base64.b64encode(f"{email}:{token}".encode()).decode()
        self.ac_field = ac_field

    def _call(self, method: str, path: str, body: dict | None = None) -> dict:
        req = urllib.request.Request(
            self.base + path,
            method=method,
            data=json.dumps(body).encode() if body is not None else None,
            headers={"Authorization": self.auth, "Accept": "application/json", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            hint = {401: " Check JIRA_EMAIL and JIRA_API_TOKEN (an Atlassian API token, not your password).",
                    403: " Your Jira account can't see or change this issue; ask the site admin for project access.",
                    404: " The issue doesn't exist on this site, or your account can't see it."}.get(e.code, "")
            raise VerifyError(f"Jira {method} {path} failed: HTTP {e.code}.{hint} {e.read()[:300]!r}") from e
        except urllib.error.URLError as e:
            raise VerifyError(f"Can't reach Jira at {self.base}: {e.reason}. Check JIRA_BASE_URL and your network.") from e

    def get_issue(self, key: str) -> dict:
        data = self._call("GET", f"/rest/api/2/issue/{key}")
        f = data.get("fields", {})
        ac = f.get(self.ac_field) if self.ac_field else None
        return {
            "key": data.get("key", key),
            "type": (f.get("issuetype") or {}).get("name", ""),
            "status": (f.get("status") or {}).get("name", ""),
            "summary": f.get("summary", ""),
            "description": f.get("description") or "",
            "acceptance_criteria": ac or "",
            "labels": f.get("labels", []),
            "reporter": (f.get("reporter") or {}).get("displayName", ""),
        }

    def add_comment(self, key: str, author: str, body: str) -> dict:
        return self._call("POST", f"/rest/api/2/issue/{key}/comment", {"body": f"[{author}]\n{body}"})

    def transition(self, key: str, status: str) -> None:
        options = self._call("GET", f"/rest/api/2/issue/{key}/transitions").get("transitions", [])
        match = next((t for t in options if t.get("to", {}).get("name", "").lower() == status.lower()), None)
        if not match:
            names = ", ".join(t.get("to", {}).get("name", "?") for t in options)
            raise VerifyError(f"No transition to '{status}' on {key}. Available: {names}")
        self._call("POST", f"/rest/api/2/issue/{key}/transitions", {"transition": {"id": match["id"]}})


def adapter(cfg: dict):
    j = expand_env(cfg.get("jira", {"adapter": "local", "path": "jira"}))
    kind = j.get("adapter", "local")
    if kind == "local":
        return LocalJira(Path(cfg["_root"]) / j.get("path", "jira"))
    if kind == "cloud":
        return CloudJira(j.get("base_url", ""), j.get("email", ""), j.get("api_token", ""), j.get("ac_field"))
    raise VerifyError(f"Unknown jira adapter '{kind}'. Use 'local' or 'cloud'.")
