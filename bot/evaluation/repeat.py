# Review saved PR contexts several times and report, per point Claude judges,
# how often the runs agree and match expected.json. Costs tokens, so it calls
# Claude only with --run; without it, it prints the plan. Not a unit test.
#
#     # Plan only, no calls: which PRs, how many calls, about how many tokens.
#     python bot/evaluation/repeat.py
#
#     # Every context, 3 runs each. --label names the round in the results file.
#     python bot/evaluation/repeat.py --run --label after
#
#     # One PR, 5 runs: recheck an unstable point after tightening its rule.
#     python bot/evaluation/repeat.py --run --runs 5 bot/evaluation/contexts/pr1561.json
#
# Only the 10 PRs in expected.json are checked (linkedin-mcp-server #1415,
# #1480, #1511, #1521, #1523, #1526, #1530, #1548, #1557, #1561). A context for
# any other PR is ignored.
#
# For the prompt suite (C5), one run per PR lists every point that disagrees
# with expected.json, marked ✗, and the per-point table counts them:
#     python bot/evaluation/repeat.py --run --runs 1 --label suite
#
# Contexts (from `review.py --save-context`) live on Google Drive,
# not in git. Put them in bot/evaluation/contexts/; only those present are run.
# Results go to bot/evaluation/out/ unless --out is given.


import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOT = HERE.parent
if str(BOT) not in sys.path:
    sys.path.insert(0, str(BOT))  # so the script finds claude_review.py and friends

import claude_review  # noqa: E402
import script_checks  # noqa: E402
from report import CRITERIA_FILE, load_parts  # noqa: E402
from review import load_context  # noqa: E402

DEFAULT_RUNS = 3
DEFAULT_EXPECTED = HERE / "expected.json"
CONTEXTS = HERE / "contexts"
OUT_DIR = HERE / "out"
ERROR = "error"  # the status shown for a run that failed


def default_contexts():
    """The context files present in bot/evaluation/contexts."""
    return sorted(CONTEXTS.glob("*.json"))


def pr_key(context):
    return f"{context['repo']}#{context['pr_number']}"


def llm_parts(parts, context):
    """criteria.json without the points script_checks.py decides."""
    _, remaining = script_checks.run(parts, context["body"])
    return remaining


def point_ids(parts):
    return [point["id"] for part in parts for point in part["points"]]


def repeat(parts, context, runs, review):
    """Call review(parts, context) `runs` times. Return one dict per run:
    {"model": ..., "results": {id: {"status", "explanation"}}}, or
    {"error": message} for a run that failed. A failed run doesn't stop the
    others, because each one has already cost tokens."""
    done = []
    for i in range(runs):
        print(f"  run {i + 1}/{runs} ...", file=sys.stderr)
        try:
            results, model = review(parts, context)
        except Exception as e:  # noqa: BLE001 - keep the other runs
            done.append({"error": f"{type(e).__name__}: {e}"})
            continue
        done.append({"model": model, "results": {r["id"]: {"status": r["status"], "explanation": r["explanation"]} for r in results}})
    return done


def summarize(ids, runs, expected):
    """One row per point: the status of each run, how many runs gave the most
    common status, and how many match the expected status. A point is stable
    when every run, failed runs included, gave the same status."""
    rows = []
    for point_id in ids:
        statuses = [ERROR if "error" in run else run["results"][point_id]["status"] for run in runs]
        agree = max(Counter(s for s in statuses if s != ERROR).values(), default=0)
        want = expected.get(point_id)
        rows.append(
            {
                "id": point_id,
                "statuses": statuses,
                "agree": agree,
                "stable": bool(runs) and agree == len(runs),
                "expected": want,
                "correct": None if want is None else sum(s == want for s in statuses),
            }
        )
    return rows


def render(key, runs, rows):
    """The agreement table for one PR, as plain text."""
    n = len(runs)
    models = sorted({run["model"] for run in runs if "error" not in run})
    failed = sum("error" in run for run in runs)
    lines = [f"{key} · {n} runs · {', '.join(models) or 'no answer'}"]
    if len(models) > 1:
        lines.append("  ⚠ the runs were answered by different models, so a disagreement may not be Claude's own")
    if failed:
        lines.append(f"  ⚠ {failed} of {n} runs failed: " + "; ".join(run["error"] for run in runs if "error" in run))
    width = max(len(row["id"]) for row in rows)
    header = "  " + "point".ljust(width) + "  " + "  ".join(f"run {i + 1}".ljust(5) for i in range(n)) + "  agree   expected"
    lines.append(header)
    for row in rows:
        cells = "  ".join(s.ljust(5) for s in row["statuses"])
        agree = f"{row['agree']}/{n}" + ("" if row["stable"] else " ←")
        if row["expected"] is None:
            want = "-"
        else:
            want = f"{row['expected']} {row['correct']}/{n}" + ("" if row["correct"] == n else " ✗")
        lines.append(f"  {row['id'].ljust(width)}  {cells}  {agree.ljust(6)}  {want}")
    return "\n".join(lines)


def render_overall(all_rows):
    """Per point, over every PR: in how many PRs it was stable and matched
    the expected status in every run."""
    ids = list(dict.fromkeys(row["id"] for rows in all_rows.values() for row in rows))
    width = max(len(i) for i in ids)
    lines = [f"Per point over {len(all_rows)} PRs", "  " + "point".ljust(width) + "  stable  all runs as expected"]
    total_stable = total_correct = total = 0
    for point_id in ids:
        rows = [row for rows in all_rows.values() for row in rows if row["id"] == point_id]
        stable = sum(row["stable"] for row in rows)
        checked = [row for row in rows if row["expected"] is not None]
        correct = sum(row["correct"] == len(row["statuses"]) for row in checked)
        total_stable, total_correct, total = total_stable + stable, total_correct + correct, total + len(rows)
        mark = "" if stable == len(rows) else " ←"
        lines.append(f"  {point_id.ljust(width)}  {f'{stable}/{len(rows)}'.ljust(6)}  {correct}/{len(checked)}{mark}")
    lines.append(f"Stable: {total_stable}/{total} · all runs as expected: {total_correct}/{total}")
    return "\n".join(lines)


def load_expected(path):
    """{"OWNER/REPO#N": {point id: status}}, or {} without the file."""
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def plan(parts, contexts, runs):
    """What --run would send, without calling Claude."""
    lines = []
    total_tokens = 0
    for path, context in contexts:
        remaining = llm_parts(parts, context)
        prompt = claude_review.build_system(remaining, context) + claude_review.build_user(context)
        tokens = len(prompt) // 4
        total_tokens += tokens * runs
        lines.append(f"  {pr_key(context)} ({path.name}): {len(point_ids(remaining))} points, ~{tokens:,} input tokens per run")
    calls = len(contexts) * runs
    lines.append(f"--run would make {calls} Claude calls ({len(contexts)} contexts × {runs} runs), ~{total_tokens:,} input tokens in total.")
    lines.append("No Claude calls were made. Add --run to make them.")
    return "\n".join(lines)


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Review saved PR contexts several times and report agreement per point.")
    parser.add_argument("contexts", nargs="*", type=Path, help="files saved with review.py --save-context (default: all in bot/evaluation/contexts)")
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS, help=f"runs per context (default {DEFAULT_RUNS})")
    parser.add_argument("--run", action="store_true", help="make the Claude calls; without it, only print the plan")
    parser.add_argument("--expected", type=Path, default=DEFAULT_EXPECTED, help="expected statuses (default bot/evaluation/expected.json)")
    parser.add_argument("--label", default="", help="a name for this round, such as before or after, saved in the output")
    parser.add_argument("--out", type=Path, help="where --run writes the results (default: a new file in bot/evaluation/out)")
    args = parser.parse_args(argv)
    if args.runs < 1:
        parser.error("--runs must be at least 1")
    return args


def main(argv=None, review=None):
    args = parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # the tables contain ← and ✗
    parts = load_parts()
    paths = args.contexts or default_contexts()
    if not paths:
        sys.exit(f"No context files in {CONTEXTS}. Download them from the team's Google Drive, or save one with:\n" "    python bot/review.py --repo OWNER/REPO --pr N --dry-run --save-context bot/evaluation/contexts/prN.json")
    expected = load_expected(args.expected)
    contexts = []
    for path in paths:
        context = load_context(path)
        if pr_key(context) in expected:
            contexts.append((path, context))
        else:
            print(f"Ignored, not in {args.expected.name}: {pr_key(context)} ({path.name})")
    if not contexts:
        sys.exit(f"None of the context files is for a PR in {args.expected}.")
    if not args.contexts:
        present = {pr_key(context) for _, context in contexts}
        for key in expected:
            if key not in present:
                print(f"Skipped, no context file: {key}")

    if not args.run:
        print(plan(parts, contexts, args.runs))
        return

    if review is None:
        try:
            claude_review.check_credentials()
        except claude_review.ReviewError as e:
            sys.exit(str(e))
        review = claude_review.review
    stamp = datetime.now(timezone.utc)
    out = args.out or OUT_DIR / f"{stamp:%Y%m%d-%H%M%S}{'-' + args.label if args.label else ''}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    saved = {
        "label": args.label,
        "created_at": stamp.isoformat(timespec="seconds"),
        "model": claude_review.MODEL,
        "effort": claude_review.EFFORT,
        "criteria_sha256": hashlib.sha256(CRITERIA_FILE.read_bytes()).hexdigest(),
        "runs_per_pr": args.runs,
        "prs": {},
    }
    all_rows = {}
    for path, context in contexts:
        key = pr_key(context)
        print(f"{key}: {args.runs} runs", file=sys.stderr)
        remaining = llm_parts(parts, context)
        runs = repeat(remaining, context, args.runs, review)
        rows = summarize(point_ids(remaining), runs, expected.get(key, {}))
        all_rows[key] = rows
        saved["prs"][key] = {"context": str(path), "head_sha": context["head_sha"], "runs": runs, "rows": rows}
        out.write_text(json.dumps(saved, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")  # after each PR
        print(render(key, runs, rows) + "\n")
    print(render_overall(all_rows))
    print(f"\nResults written to {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
