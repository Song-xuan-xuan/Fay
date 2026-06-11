import shutil
from datetime import datetime
from pathlib import Path


DEFAULT_MAX_ARCHIVE_BATCHES = 10


def archive_startup_artifacts(batch_id=None, max_archives=DEFAULT_MAX_ARCHIVE_BATCHES):
    batch = batch_id or _batch_id()
    return {
        "samples": archive_runtime_files(
            "samples",
            lambda name: name.startswith("sample-"),
            batch,
            max_archives,
        ),
        "logs": archive_runtime_files(
            "logs",
            lambda name: name.endswith(".log"),
            batch,
            max_archives,
        ),
    }


def archive_runtime_files(base_dir, matcher, batch_id=None, max_archives=DEFAULT_MAX_ARCHIVE_BATCHES):
    base = Path(base_dir)
    base.mkdir(parents=True, exist_ok=True)
    files = [path for path in base.iterdir() if path.is_file() and matcher(path.name)]
    archive_root = base / "archive"
    if not files:
        _prune_archive_batches(archive_root, max_archives)
        return 0

    target = archive_root / (batch_id or _batch_id())
    target.mkdir(parents=True, exist_ok=True)
    moved = 0
    for source in files:
        destination = _unique_path(target / source.name)
        try:
            shutil.move(str(source), str(destination))
            moved += 1
        except PermissionError:
            continue
    _prune_archive_batches(archive_root, max_archives)
    return moved


def _batch_id():
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _unique_path(path):
    if not path.exists():
        return path
    index = 1
    while True:
        candidate = path.with_name(f"{path.stem}-{index}{path.suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def _prune_archive_batches(archive_root, max_archives):
    if max_archives <= 0 or not archive_root.exists():
        return
    batches = [path for path in archive_root.iterdir() if path.is_dir()]
    batches.sort(key=lambda path: (path.stat().st_mtime, path.name))
    for path in batches[:-max_archives]:
        _remove_archive_dir(archive_root, path)


def _remove_archive_dir(archive_root, path):
    try:
        path.resolve().relative_to(archive_root.resolve())
    except ValueError:
        return
    shutil.rmtree(path)
