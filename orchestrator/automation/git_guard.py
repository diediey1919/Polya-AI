"""
Git Source-of-Truth Guard.
Validates repository identity, captures commit SHAs, and ensures Git integrity.
Does NOT clean, modify, or stash dirty worktrees.
"""
import subprocess
from pathlib import Path
from typing import NamedTuple, Optional


class GitIdentity(NamedTuple):
    commit_sha: str
    branch: str
    is_dirty: bool
    remote_url: Optional[str] = None


class GitGuardError(Exception):
    """Raised when Git repository or identity verification fails."""
    pass


class GitGuard:
    def __init__(self, repo_path: str = "/home/ubuntu/Polya-AI"):
        self.repo_path = Path(repo_path).resolve()

    def get_current_identity(self) -> GitIdentity:
        """Retrieves and verifies the current Git repository identity."""
        if not (self.repo_path / ".git").exists() and not (self.repo_path / ".git").is_file():
            # Could be a worktree or standard repo
            # Run git rev-parse --git-dir to verify
            try:
                res = subprocess.run(
                    ["git", "rev-parse", "--git-dir"],
                    cwd=str(self.repo_path),
                    capture_output=True,
                    text=True,
                    check=True
                )
            except Exception as e:
                raise GitGuardError(f"Directory {self.repo_path} is not a valid Git repository: {e}")

        try:
            # Commit SHA
            sha_res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                check=True
            )
            commit_sha = sha_res.stdout.strip()
            if not commit_sha or len(commit_sha) != 40:
                raise GitGuardError(f"Invalid commit SHA obtained: {commit_sha}")

            # Branch
            branch_res = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                check=True
            )
            branch = branch_res.stdout.strip()

            # Dirty check
            status_res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                check=True
            )
            is_dirty = bool(status_res.stdout.strip())

            # Remote URL (optional)
            remote_res = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                cwd=str(self.repo_path),
                capture_output=True,
                text=True
            )
            remote_url = remote_res.stdout.strip() if remote_res.returncode == 0 else None

            return GitIdentity(
                commit_sha=commit_sha,
                branch=branch,
                is_dirty=is_dirty,
                remote_url=remote_url
            )
        except subprocess.CalledProcessError as e:
            raise GitGuardError(f"Git command failed: {e.stderr}")
        except Exception as e:
            raise GitGuardError(f"Git inspection error: {e}")

    def verify_commit_match(self, expected_commit_sha: str) -> bool:
        """Verifies that the current repository HEAD matches expected commit SHA."""
        if not expected_commit_sha or len(expected_commit_sha) != 40:
            return False
        try:
            current = self.get_current_identity()
            return current.commit_sha.lower() == expected_commit_sha.lower()
        except GitGuardError:
            return False
