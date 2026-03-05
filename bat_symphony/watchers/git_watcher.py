"""Poll local Git repos for new commits."""

from __future__ import annotations

import subprocess
from typing import Any


class GitWatcher:
    def __init__(self, repos: list[str]):
        self._repos = repos
        self._last_heads: dict[str, str] = {}

    def get_head(self, repo_path: str) -> str:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    def poll(self) -> list[dict[str, Any]]:
        changes = []
        for repo in self._repos:
            try:
                head = self.get_head(repo)
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
            old_head = self._last_heads.get(repo)
            if old_head is not None and head != old_head:
                changes.append({
                    "repo": repo,
                    "old_head": old_head,
                    "new_head": head,
                })
            self._last_heads[repo] = head
        return changes

    def get_commit_log(self, repo_path: str, since_sha: str, limit: int = 10) -> list[dict[str, str]]:
        result = subprocess.run(
            ["git", "log", f"{since_sha}..HEAD", f"--max-count={limit}", "--format=%H|%s|%an|%ai"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|", 3)
            if len(parts) == 4:
                commits.append({
                    "sha": parts[0],
                    "subject": parts[1],
                    "author": parts[2],
                    "date": parts[3],
                })
        return commits
