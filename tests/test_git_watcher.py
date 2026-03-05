import subprocess
import tempfile
from pathlib import Path

from bat_symphony.watchers.git_watcher import GitWatcher


def _init_repo(path: Path):
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True, capture_output=True)
    (path / "README.md").write_text("init")
    subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=path, check=True, capture_output=True)


def test_get_head():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "test-repo"
        repo.mkdir()
        _init_repo(repo)
        watcher = GitWatcher(repos=[str(repo)])
        head = watcher.get_head(str(repo))
        assert len(head) == 40


def test_detect_change():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "test-repo"
        repo.mkdir()
        _init_repo(repo)
        watcher = GitWatcher(repos=[str(repo)])
        changes = watcher.poll()
        assert len(changes) == 0  # first poll establishes baseline

        (repo / "new.txt").write_text("change")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add"], cwd=repo, check=True, capture_output=True)

        changes = watcher.poll()
        assert len(changes) == 1
        assert changes[0]["repo"] == str(repo)
        assert changes[0]["old_head"] != changes[0]["new_head"]
