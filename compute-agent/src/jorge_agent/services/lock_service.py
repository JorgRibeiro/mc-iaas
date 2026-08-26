import fcntl
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from jorge_agent.config import PATHS


INSTANCE_LOCKS_DIR = PATHS.lock_dir / "instances"
RUNTIME_LOCK_PATH = PATHS.lock_dir / "runtime.lock"


def _validate_instance_name(name: str) -> None:
    if (
        not name
        or "/" in name
        or "\\" in name
        or name in {".", ".."}
    ):
        raise ValueError(
            f"Invalid instance name for lock: {name!r}"
        )


@contextmanager
def _exclusive_file_lock(
    path: Path,
) -> Generator[None, None, None]:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        mode="a+",
        encoding="utf-8",
    ) as lock_file:
        fcntl.flock(
            lock_file.fileno(),
            fcntl.LOCK_EX,
        )

        try:
            yield
        finally:
            fcntl.flock(
                lock_file.fileno(),
                fcntl.LOCK_UN,
            )


@contextmanager
def runtime_lock() -> Generator[None, None, None]:
    """
    Serialize operations that mutate global runtime resources.
    """

    with _exclusive_file_lock(
        RUNTIME_LOCK_PATH
    ):
        yield


@contextmanager
def instance_lock(
    name: str,
) -> Generator[None, None, None]:
    """
    Serialize mutable operations for a single instance.
    """

    _validate_instance_name(name)

    lock_path = (
        INSTANCE_LOCKS_DIR
        / f"{name}.lock"
    )

    with _exclusive_file_lock(
        lock_path
    ):
        yield


@contextmanager
def instance_runtime_lock(
    name: str,
) -> Generator[None, None, None]:
    """
    Acquire both locks using the mandatory order:

        instance lock -> runtime lock
    """

    with instance_lock(name):
        with runtime_lock():
            yield