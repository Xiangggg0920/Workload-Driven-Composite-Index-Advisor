"""Optional terminal display; never reads artifacts or queries PostgreSQL."""
from __future__ import annotations

import sys


class LiveProgress:
    def __init__(self, stream=None):
        self.stream = sys.stderr if stream is None else stream
        self.width = 0
        try:
            self.live = bool(self.stream.isatty())
        except Exception:
            self.live = False

    def _plain(self, line):
        # A closed/redirected/broken display must not affect the experiment.
        try:
            self.stream.write(line + "\n")
            self.stream.flush()
        except Exception:
            pass

    def _render(self, line, finished):
        self.stream.write("\r" + line + " " * max(0, self.width - len(line)))
        if finished:
            self.stream.write("\n")
        self.stream.flush()
        self.width = 0 if finished else len(line)

    def __call__(self, event):
        try:
            done, total = event["completed"], event["total"]
            filled = 16 * done // max(1, total)
            bar = "#" * filled + "." * (16 - filled)
            strategy = {"baseline": "Baseline", "single": "Single",
                        "suboptimal": "Suboptimal", "advisor": "Advisor"}.get(event["strategy"], "-")
            status = {"complete_with_infeasible_configurations": "complete/budget_exceeded"}.get(
                event["status"], event["status"])
            line = (f"[{bar}] {done}/{total} R{event['round']}/{event['rounds']} "
                    f"{strategy} {event['budget_mib']}MiB {status}")
            finished = event["status"] in {"complete", "complete_with_infeasible_configurations",
                                            "failed", "cleanup_required"}
        except Exception:
            self.live = False
            self._plain("Progress unavailable; benchmark continues with normal output.")
            return
        if self.live:
            try:
                self._render(line, finished)
                return
            except Exception:
                self.live = False
                self._plain("\nLive progress unavailable; using text output.")
        self._plain(line)
