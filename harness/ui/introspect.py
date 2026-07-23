"""Repo-dictated UI: introspect the repository into ``ui_manifest.json``.

The dashboard's design is a *projection of the repo* — nothing here is
hand-curated. Sources of truth:

  * generator families  -> every (``X_PARAMS``, ``x_corpus``) pair in
    ``openvector_bench.generator_search``; knob slider specs are the
    ``(name, lo, hi, default)`` tuples themselves; knob tooltips are the
    trailing ``#`` comments in the source.
  * gate axes           -> ``GATES`` / ``MANDATORY``.
  * data panels         -> ``results/*.json``, shape-sniffed into panel kinds
    (swarm | cells | wp5 | generic); unknown shapes degrade to a generic
    card, so a new artifact type never breaks the build.
  * registration cards  -> ``results/*.md`` paired by stem
    (``X_PREDICTION.md`` <-> ``X_RESULT.md`` or the ``GEN_ROUND*`` docs),
    each with its first-line title.
  * status board        -> the WP ledger table in ``spec/NORMAL_FORMS.md``.

Run ``python -m harness.ui.build`` to regenerate the dashboard.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


# --------------------------------------------------------------------------- #
# Families (knobs + tooltips)                                                  #
# --------------------------------------------------------------------------- #


def _knob_tooltips(source: str, const_name: str, knobs: list[str]) -> dict[str, str]:
    """Best-effort: trailing # comments inside the ``const_name = (...)`` block."""
    m = re.search(rf"^{const_name}\s*[:=]", source, re.M)
    if not m:
        return {}
    depth, i, start = 0, source.index("(", m.start()), source.index("(", m.start())
    for i in range(start, len(source)):
        depth += source[i] == "("
        depth -= source[i] == ")"
        if depth == 0:
            break
    block = source[start : i + 1]
    tips: dict[str, str] = {}
    for name in knobs:
        pos = block.find(f'"{name}"')
        if pos < 0:
            continue
        # collect comments from the knob's line to the next knob's quoted name
        nxt = min(
            (p for p in (block.find(f'"{k}"', pos + 1) for k in knobs) if p > pos),
            default=len(block),
        )
        tips[name] = " ".join(
            c.strip() for c in re.findall(r"#\s*(.+)", block[pos:nxt])
        ).strip()
    return tips


def families() -> list[dict]:
    import openvector_bench.generator_search as gs

    src_path = gs.__file__
    with open(src_path, encoding="utf-8") as f:
        source = f.read()
    out = []
    for attr in sorted(dir(gs)):
        if not attr.endswith("_PARAMS"):
            continue
        stem = attr[: -len("_PARAMS")].lower()
        fn_name = next(
            (
                n
                for n in (
                    f"{stem}_corpus",
                    "synth_corpus" if attr == "PARAMS" else None,
                )
                if n and hasattr(gs, n)
            ),
            None,
        )
        # HIER_MS -> hier_multiscale etc.: fall back to scanning for a match
        if fn_name is None:
            cands = [
                n
                for n in dir(gs)
                if n.endswith("_corpus") and n.startswith(stem.split("_")[0])
            ]
            fn_name = cands[0] if len(cands) == 1 else None
        spec = getattr(gs, attr)
        knobs = [
            {"name": n, "lo": lo, "hi": hi, "default": d} for (n, lo, hi, d) in spec
        ]
        tips = _knob_tooltips(source, attr, [k["name"] for k in knobs])
        for k in knobs:
            k["tooltip"] = tips.get(k["name"], "")
        fn = getattr(gs, fn_name, None) if fn_name else None
        out.append(
            {
                "params_const": attr,
                "family": stem,
                "fn": fn_name,
                "doc": (fn.__doc__ or "").strip().split("\n\n")[0] if fn else "",
                "knobs": knobs,
            }
        )
    return out


# --------------------------------------------------------------------------- #
# Results (shape-sniffed)                                                      #
# --------------------------------------------------------------------------- #


def _sniff(name: str, d) -> dict:
    if (
        isinstance(d, dict)
        and isinstance(d.get("shards"), list)
        and d["shards"]
        and isinstance(d["shards"][0], dict)
        and "params" in d["shards"][0]
    ):
        return {"kind": "swarm", "file": name, "shards": d["shards"]}
    if isinstance(d, list) and d and isinstance(d[0], dict) and "g1_id_twonn" in d[0]:
        return {"kind": "cells", "file": name, "cells": d}
    if isinstance(d, dict) and "curves" in d and "verdict" in d:
        return {
            "kind": "wp5",
            "file": name,
            "curves": d["curves"],
            "verdict": d["verdict"],
            "p3": d.get("p3", {}),
        }
    keys = list(d.keys())[:12] if isinstance(d, dict) else [f"list[{len(d)}]"]
    return {"kind": "generic", "file": name, "keys": keys}


def results() -> list[dict]:
    out = []
    rdir = os.path.join(REPO, "results")
    for f in sorted(os.listdir(rdir)):
        if not f.endswith(".json"):
            continue
        try:
            with open(os.path.join(rdir, f), encoding="utf-8") as fh:
                out.append(_sniff(f, json.load(fh)))
        except (json.JSONDecodeError, OSError) as e:
            out.append({"kind": "unreadable", "file": f, "error": str(e)})
    return out


# --------------------------------------------------------------------------- #
# Docs (registration cards) + WP ledger                                        #
# --------------------------------------------------------------------------- #


def docs() -> list[dict]:
    rdir = os.path.join(REPO, "results")
    entries = {}
    for f in sorted(os.listdir(rdir)):
        if not f.endswith(".md"):
            continue
        with open(os.path.join(rdir, f), encoding="utf-8") as fh:
            title = fh.readline().lstrip("# ").strip()
        stem = re.sub(r"_(PREDICTION|RESULT)\.md$", "", f)
        stem = stem.removesuffix(".md")
        e = entries.setdefault(stem, {"stem": stem})
        if f.endswith("_PREDICTION.md"):
            e["prediction"], e["prediction_title"] = f, title
        elif f.endswith("_RESULT.md"):
            e["result"], e["result_title"] = f, title
        else:
            e["doc"], e["title"] = f, title
    return list(entries.values())


def ledger() -> list[dict]:
    path = os.path.join(REPO, "spec", "NORMAL_FORMS.md")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        text = f.read()
    rows = []
    for m in re.finditer(
        r"^\|\s*\*\*(WP\d)\*\*\s*([^|]*)\|\s*\*\*([^*|]+)\*\*[^|]*\|\s*([^|]+)\|",
        text,
        re.M,
    ):
        rows.append(
            {
                "wp": m.group(1),
                "name": m.group(2).strip(),
                "status": m.group(3).strip(),
                "evidence": m.group(4).strip()[:200],
            }
        )
    return rows


# --------------------------------------------------------------------------- #
# Manifest                                                                     #
# --------------------------------------------------------------------------- #


def build_manifest() -> dict:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            cwd=REPO,
            check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        commit = "unknown"
    import openvector_bench.generator_search as gs

    return {
        "generated_at": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()),
        "commit": commit,
        "gates": {"list": list(gs.GATES), "mandatory": sorted(gs.MANDATORY)},
        "families": families(),
        "results": results(),
        "docs": docs(),
        "ledger": ledger(),
    }


if __name__ == "__main__":
    print(json.dumps(build_manifest(), indent=1)[:2000])
