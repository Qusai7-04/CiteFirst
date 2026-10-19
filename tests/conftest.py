"""Shared fixtures and helpers for the CiteFirst test suite."""
import os
import pytest


def _can_symlink(tmp: os.PathLike) -> bool:
    """Return True if the current process can create symlinks in tmp."""
    probe = os.path.join(tmp, ".symlink_probe")
    target = os.path.join(tmp, ".symlink_target")
    try:
        open(target, "w").close()
        os.symlink(target, probe)
        return True
    except OSError:
        return False
    finally:
        for p in (probe, target):
            try:
                os.unlink(p)
            except OSError:
                pass


@pytest.fixture(autouse=True)
def _skip_symlink_tests_on_windows(request, tmp_path):
    """Auto-skip tests that require symlink privileges on unprivileged Windows."""
    marker = request.node.get_closest_marker("needs_symlinks")
    if marker is not None and not _can_symlink(tmp_path):
        pytest.skip("Symlink creation requires elevated privileges on this Windows system")
