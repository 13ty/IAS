"""
Shallow Git Clone with Windows-safe cleanup for IAS Pipeline.

Uses GitPython for cloning, handles read-only files on Windows.
"""

import os
import shutil
import stat
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Optional
from git import Repo, GitCommandError


class CloneError(Exception):
    """Raised when clone operation fails."""

    pass


@contextmanager
def temporary_clone(
    repo_url: str,
    target_dir: Path,
    branch: str = "HEAD",
    depth: int = 1,
    single_branch: bool = True,
):
    """
    Context manager for shallow clone with guaranteed cleanup.

    Usage:
        with temporary_clone(url, Path("/tmp/my_repo")) as repo_path:
            # work with repo_path
            pass
        # Automatically cleaned up on exit
    """
    # Ensure parent exists
    target_dir.parent.mkdir(parents=True, exist_ok=True)

    # Windows: use short temp path to avoid MAX_PATH issues
    if os.name == "nt":
        # Try to use C:\tmp if available, else system temp
        short_tmp = Path("C:/tmp")
        try:
            short_tmp.mkdir(exist_ok=True)
            temp_base = short_tmp
        except (OSError, PermissionError):
            temp_base = Path(tempfile.gettempdir())
    else:
        temp_base = Path(tempfile.gettempdir())

    # Create unique temp directory
    td = tempfile.TemporaryDirectory(
        prefix="ias_clone_",
        dir=temp_base,
        ignore_cleanup_errors=False,
    )

    try:
        clone_path = Path(td.name) / "source"
        print(f"[clone] Cloning {repo_url} -> {clone_path} (depth={depth})")

        Repo.clone_from(
            repo_url,
            str(clone_path),
            depth=depth,
            branch=branch if branch != "HEAD" else None,
            single_branch=single_branch,
        )

        # Copy to target if different from temp
        if clone_path != target_dir:
            if target_dir.exists():
                _safe_rmtree(target_dir)
            shutil.copytree(clone_path, target_dir)
            print(f"[clone] Copied to {target_dir}")

        yield target_dir

    except GitCommandError as e:
        raise CloneError(f"Git clone failed: {e}") from e
    except Exception as e:
        raise CloneError(f"Clone operation failed: {e}") from e
    finally:
        _safe_cleanup_tempdir(td)


def clone_to_target(
    repo_url: str,
    target_dir: Path,
    branch: str = "HEAD",
    depth: int = 1,
) -> bool:
    """
    Clone repo directly to target directory (no temp copy).
    Returns True on success, False on failure.
    """
    try:
        target_dir.parent.mkdir(parents=True, exist_ok=True)

        if target_dir.exists():
            _safe_rmtree(target_dir)

        Repo.clone_from(
            repo_url,
            str(target_dir),
            depth=depth,
            branch=branch if branch != "HEAD" else None,
            single_branch=True,
        )
        print(f"[clone] Cloned {repo_url} -> {target_dir}")
        return True

    except GitCommandError as e:
        print(f"[clone] ERROR: Git clone failed: {e}")
        return False
    except Exception as e:
        print(f"[clone] ERROR: Unexpected error: {e}")
        return False


def _safe_rmtree(path: Path) -> None:
    """Windows-safe rmtree handling read-only files."""
    if not path.exists():
        return

    if os.name == "nt":
        # Try GitPython's rmtree first (handles .git read-only)
        try:
            from git.util import rmtree as git_rmtree

            git_rmtree(str(path))
            return
        except ImportError:
            pass
        except Exception:
            pass

    # Fallback: manual read-only removal
    def handle_remove_readonly(func, path, exc_info):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    shutil.rmtree(path, onexc=handle_remove_readonly)


def _safe_cleanup_tempdir(td: tempfile.TemporaryDirectory) -> None:
    """Clean up TemporaryDirectory with Windows-safe handling."""
    try:
        if os.name == "nt":
            _safe_rmtree(Path(td.name))
        else:
            td.cleanup()
    except Exception as e:
        print(f"[clone] WARNING: Cleanup failed: {e}")


def get_repo_info(repo_path: Path) -> dict:
    """Extract basic info from cloned repo."""
    info = {
        "has_git": False,
        "branch": "unknown",
        "commit": "unknown",
        "remote_url": "unknown",
    }

    try:
        repo = Repo(repo_path)
        info["has_git"] = True
        info["branch"] = (
            repo.active_branch.name if not repo.head.is_detached else "detached"
        )
        info["commit"] = repo.head.commit.hexsha[:8]
        if repo.remotes:
            info["remote_url"] = repo.remotes[0].url
        repo.close()
    except Exception:
        pass

    return info
