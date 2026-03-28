#!/usr/bin/env python
"""
Clean up old E2E test artifacts (logs, screenshots, reports).
Keeps last N days of data.
Usage:
    python tools/cleanup_artifacts.py --days 30 logs/e2e/
"""
import argparse
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

def cleanup_artifacts(base_dir: Path, days_to_keep: int = 30):
    """Remove artifact directories older than days_to_keep."""
    cutoff = datetime.now() - timedelta(days=days_to_keep)
    removed_count = 0
    freed_space = 0

    if not base_dir.exists():
        print(f"Directory not found: {base_dir}")
        return

    for item in base_dir.iterdir():
        if not item.is_dir():
            continue

        # Check directory mtime
        mtime = datetime.fromtimestamp(item.stat().st_mtime)
        if mtime < cutoff:
            # Calculate size before deletion
            size = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
            # Delete directory tree
            try:
                shutil.rmtree(item)
                removed_count += 1
                freed_space += size
                print(f"Deleted: {item.name} ({size // (1024*1024)} MB)")
            except Exception as e:
                print(f"Failed to delete {item.name}: {e}")

    print(f"\n✓ Removed {removed_count} old artifact directories")
    print(f"✓ Freed ~{freed_space // (1024*1024)} MB")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30, help="Days of artifacts to keep")
    parser.add_argument("directory", type=Path, help="Artifact directory (e.g., logs/e2e/)")
    args = parser.parse_args()

    if not args.directory.exists():
        print(f"ERROR: Directory not found: {args.directory}")
        return 1

    cleanup_artifacts(args.directory, args.days)
    return 0

if __name__ == "__main__":
    sys.exit(main())
