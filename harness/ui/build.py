"""Build the repo-dictated dashboard: introspect -> inject -> one HTML file.

    python -m harness.ui.build [output.html]

The output is fully self-contained (manifest + all panel data inlined); default
output path is ``ui_dashboard.html`` at the repo root (gitignored — the
dashboard is a *projection* of the repo, not a source file).
"""

from __future__ import annotations

import json
import os
import sys

from .introspect import REPO, build_manifest


def build(out_path: str | None = None) -> str:
    out_path = out_path or os.path.join(REPO, "ui_dashboard.html")
    with open(os.path.join(os.path.dirname(__file__), "template.html"),
              encoding="utf-8") as f:
        template = f.read()
    manifest = build_manifest()
    payload = json.dumps(manifest, separators=(",", ":"))
    # </script> inside JSON strings would terminate the data block early.
    payload = payload.replace("</", "<\\/")
    html = template.replace("__OVB_DATA__", payload)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path


if __name__ == "__main__":
    path = build(sys.argv[1] if len(sys.argv) > 1 else None)
    print(f"wrote {path} ({os.path.getsize(path) // 1024} KB)")
