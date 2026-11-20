"""Monitor completed immutable cell files without opening the live journal.

On Windows an open reader can prevent atomic replacement of journal.json.
Never read that file during execution. Read only the short prefix of cell
artifacts, which the controller never replaces, after a settling interval.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    completed = []
    counts = Counter()
    now = time.time()
    for path in args.run_dir.glob("r*b*s*.json"):
        if path.name.endswith(".runner.json") or now - path.stat().st_mtime < 3:
            continue
        with path.open("rb") as stream:
            prefix = stream.read(8192).decode("utf-8", errors="ignore")
        match = re.search(r'"status"\s*:\s*"([^"]+)"', prefix)
        if match:
            completed.append(path)
            counts[match.group(1)] += 1
    latest = max(completed, key=lambda p: p.stat().st_mtime).name if completed else None
    summary_path = args.run_dir / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else None
    print(json.dumps({"checked_at": datetime.now(timezone.utc).isoformat(),
                      "run_directory_exists": args.run_dir.is_dir(),
                      "completed_cell_files": len(completed), "statuses": dict(counts),
                      "latest": latest, "controller_finished": summary is not None,
                      "final_status": summary["status"] if summary else None, "live_journal_opened": False}))


if __name__ == "__main__":
    main()
