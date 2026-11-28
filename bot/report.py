# Render a review report as a Markdown PR comment.
#
# A report is a dict like the one in sample_report.json. Its "criteria" list
# holds one result per point in criteria.json:
#
#     {"id": "...", "status": "pass" | "fail" | "n/a",
#      "explanation": "...", "requested_change": "..."}
#
# The score gives each part an equal share of 100 points, split evenly among
# the part's points. Points marked "n/a" don't count.
#
# The comment layout lives in the templates below. Edit them to change how the
# comment looks; the code only fills in the placeholders.


import json
from pathlib import Path

TEMPLATE = """\
<!-- pr-bot-report -->
## 🤖 PR review: {score}/100 · {verdict}

Reviewed commit `{commit}` · requested by `{requester}`

| Part | Point | Result |
|---|---|:-:|
{table_rows}
{fix_section}
---
<sub>This bot only advises. A maintainer decides whether to merge. After you push a fix, ask a maintainer to comment <code>/review</code> again.</sub>
"""

ROW_TEMPLATE = "| {part} | {label} | {icon} |"

FIX_SECTION_TEMPLATE = "\n### What to fix\n{fix_parts}"

FIX_PART_TEMPLATE = "\n**{part}**\n\n{fix_items}"

FIX_ITEM_TEMPLATE = "- [ ] **{label}:** {explanation}{suggestion}"

SUGGESTION_TEMPLATE = "\n  - Suggested: {requested_change}"

VERDICT_FAIL = "Changes requested"

VERDICT_PASS = "Ready for human review"

ICONS = {"pass": "✅", "fail": "❌", "n/a": "➖"}

CRITERIA_FILE = Path(__file__).with_name("criteria.json")

CHECK_TYPES = {"llm", "script"}


def load_parts(path=CRITERIA_FILE):
    """Load criteria.json and fail early with a clear message if it's malformed.

    A point Claude judges also has "fail_if", a list of conditions that make it
    fail, and may have "na_if", the one case where it doesn't apply.
    claude_review.build_system checks that every point it sends has fail_if."""
    parts = json.loads(path.read_text(encoding="utf-8"))["parts"]
    if not parts:
        raise ValueError("criteria.json has no parts")

    seen = set()
    for part in parts:
        if not part.get("points"):
            raise ValueError(f"Part '{part['id']}' in criteria.json has no points")
        for point in part["points"]:
            if point["id"] in seen:
                raise ValueError(f"Point id '{point['id']}' appears twice in criteria.json")
            if point["check"] not in CHECK_TYPES:
                raise ValueError(f"Point '{point['id']}' has unknown check '{point['check']}'")
            for field in ("label", "question"):
                if not point.get(field):
                    raise ValueError(f"Point '{point['id']}' in criteria.json has no '{field}'")
            fail_if = point.get("fail_if", [])
            if not isinstance(fail_if, list) or not all(isinstance(c, str) and c.strip() for c in fail_if):
                raise ValueError(f"Point '{point['id']}' in criteria.json: 'fail_if' must be a list of non-empty strings")
            if "na_if" in point and not (isinstance(point["na_if"], str) and point["na_if"].strip()):
                raise ValueError(f"Point '{point['id']}' in criteria.json: 'na_if' must be a non-empty string")
            seen.add(point["id"])
    return parts


def _applicable(part, results):
    return [p for p in part["points"] if results[p["id"]]["status"] != "n/a"]


def _passed(points, results):
    return sum(1 for p in points if results[p["id"]]["status"] == "pass")


def _one_line(text):
    """Collapse newlines and extra spaces, so text from the LLM can't break the layout."""
    return " ".join(str(text).split())


def compute_score(parts, results):
    share = 100 / len(parts)
    score = 0.0
    for part in parts:
        applicable = _applicable(part, results)
        if not applicable:
            score += share
            continue
        score += share * _passed(applicable, results) / len(applicable)
    return round(score)


def _table_rows(parts, results):
    rows = []
    for part in parts:
        applicable = _applicable(part, results)
        tally = f" ({_passed(applicable, results)}/{len(applicable)})" if applicable else ""
        for i, point in enumerate(part["points"]):
            rows.append(
                ROW_TEMPLATE.format(
                    part=f"**{part['title']}**{tally}" if i == 0 else "",
                    label=point["label"],
                    icon=ICONS[results[point["id"]]["status"]],
                )
            )
    return "\n".join(rows)


def _fix_section(parts, results):
    fix_parts = []
    for part in parts:
        items = []
        for point in part["points"]:
            result = results[point["id"]]
            if result["status"] != "fail":
                continue
            change = _one_line(result.get("requested_change", ""))
            items.append(
                FIX_ITEM_TEMPLATE.format(
                    label=point["label"],
                    explanation=_one_line(result.get("explanation", "")),
                    suggestion=SUGGESTION_TEMPLATE.format(requested_change=change) if change else "",
                )
            )
        if items:
            fix_parts.append(FIX_PART_TEMPLATE.format(part=part["title"], fix_items="\n".join(items)))

    if not fix_parts:
        return ""
    return FIX_SECTION_TEMPLATE.format(fix_parts="\n".join(fix_parts))


def render(report):
    parts = load_parts()
    results = {c["id"]: c for c in report["criteria"]}

    expected = {p["id"] for part in parts for p in part["points"]}
    missing = expected - results.keys()
    if missing:
        raise ValueError(f"Report has no result for: {', '.join(sorted(missing))}")

    failed = any(results[i]["status"] == "fail" for i in expected)

    return TEMPLATE.format(
        score=compute_score(parts, results),
        verdict=VERDICT_FAIL if failed else VERDICT_PASS,
        commit=report["head_sha"][:7],
        requester=report["requested_by"],
        table_rows=_table_rows(parts, results),
        fix_section=_fix_section(parts, results),
    )
