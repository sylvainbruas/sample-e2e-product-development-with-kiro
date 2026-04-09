#!/usr/bin/env python3
"""
al-dt-evaluate.py — Design Thinking evaluation operations.

Calculates weighted scores for idea evaluation matrices.

Usage:
  al-dt-evaluate.py score --module MOD --scores REL_PATH --criteria REL_PATH --output REL_PATH

Paths are module-relative, resolved to .al/output/{module}/.

scores: JSON with item scores
  { "items": [ { "name": "...", "scores": { "criterion": 1-5, ... } } ] }
  Also accepts "ideas" or "concepts" as the key name.

criteria: JSON with criteria and weights
  { "criteria": [ { "name": "...", "weight": 3 } ] }

Output: ranked evaluation matrix as markdown artifact.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def cmd_score(args):
    """Calculate weighted scores and produce ranked matrix."""
    # Resolve paths
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(scripts_dir, "..", "..", "..", "runtime", "scripts"))
    try:
        from al_paths import resolve_path
    except ImportError:
        sys.path.insert(0, os.path.join(scripts_dir, "..", "..", "..", "..", "runtime", "scripts"))
        from al_paths import resolve_path

    scores_path = resolve_path(args.module, args.scores) if args.module else args.scores
    criteria_path = resolve_path(args.module, args.criteria) if args.module else args.criteria
    output_path = resolve_path(args.module, args.output) if args.module else args.output

    if not os.path.exists(scores_path):
        print(json.dumps({"status": "error", "message": f"File not found: {args.scores}"}))
        sys.exit(1)
    if not os.path.exists(criteria_path):
        print(json.dumps({"status": "error", "message": f"File not found: {args.criteria}"}))
        sys.exit(1)

    with open(scores_path, encoding="utf-8") as f:
        scores_data = json.load(f)
    with open(criteria_path, encoding="utf-8") as f:
        criteria_data = json.load(f)

    criteria = criteria_data["criteria"]
    items = scores_data.get("items") or scores_data.get("ideas") or scores_data.get("concepts", [])

    max_possible = sum(c["weight"] * 5 for c in criteria)

    # Calculate weighted totals
    ranked = []
    for item in items:
        total = 0
        breakdown = {}
        for c in criteria:
            raw = item["scores"].get(c["name"], 0)
            weighted = raw * c["weight"]
            total += weighted
            breakdown[c["name"]] = {"raw": raw, "weight": c["weight"], "weighted": weighted}
        pct = round((total / max_possible) * 100, 1) if max_possible > 0 else 0
        ranked.append({
            "name": item["name"],
            "total": total,
            "percentage": pct,
            "breakdown": breakdown,
        })

    ranked.sort(key=lambda x: x["total"], reverse=True)

    # Generate markdown
    lines = ["# Evaluation Matrix"]
    lines.append("")

    # Criteria summary
    lines.append("## Criteria")
    lines.append("")
    lines.append("| Criterion | Weight |")
    lines.append("|-----------|--------|")
    for c in criteria:
        lines.append(f"| {c['name']} | {c['weight']}x |")
    lines.append("")

    # Results table
    header_cols = ["Rank", "Item"] + [c["name"] for c in criteria] + ["Total", "%"]
    lines.append("## Rankings")
    lines.append("")
    lines.append("| " + " | ".join(header_cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(header_cols)) + " |")

    for i, item in enumerate(ranked, 1):
        cols = [str(i), item["name"]]
        for c in criteria:
            b = item["breakdown"][c["name"]]
            cols.append(f"{b['raw']} ({b['weighted']})")
        cols.append(str(item["total"]))
        cols.append(f"{item['percentage']}%")
        lines.append("| " + " | ".join(cols) + " |")

    lines.append("")

    # Write output
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(json.dumps({
        "status": "ok",
        "path": output_path,
        "ranked": [{"rank": i + 1, "name": r["name"], "total": r["total"], "percentage": r["percentage"]} for i, r in enumerate(ranked)],
    }))


def main():
    parser = argparse.ArgumentParser(description="Design Thinking evaluation operations")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("score", help="Calculate weighted scores and rank ideas")
    p.add_argument("--module", required=True, help="Module name")
    p.add_argument("--scores", required=True, help="Module-relative path to scores JSON")
    p.add_argument("--criteria", required=True, help="Module-relative path to criteria JSON")
    p.add_argument("--output", required=True, help="Module-relative output path")

    args = parser.parse_args()
    commands = {
        "score": cmd_score,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
