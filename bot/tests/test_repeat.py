# Written by AI (Claude Opus 5.5 in Claude Code). Claude is faked: every test
# passes its own review function, and any real API client raises, so no test
# can cost tokens. Run with:
#     python -m unittest discover -s bot

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import claude_review
import review as review_cli
from evaluation import repeat
from report import load_parts

PARTS = load_parts()
CONTEXT = {
    "repo": "user/demo",
    "pr_number": 7,
    "title": "Add greeting",
    "body": "## Summary\n\nAdds a greeting.\n\n## Verification\n\n- ran it\n\n## Synthetic prompt\n\n> add a greeting",
    "author": "contributor",
    "base_ref": "main",
    "base_sha": "b" * 40,
    "head_sha": "h" * 40,
    "commit_messages": ["add greeting"],
    "linked_issues": [],
    "guides": {},
    "tree": ["hello.py"],
    "files": [],
    "omitted": [],
}
LLM_PARTS = repeat.llm_parts(PARTS, CONTEXT)
IDS = repeat.point_ids(LLM_PARTS)


def fake_review(*answers, model="claude-opus-5-5"):
    """A review function that answers from `answers`, one per call: a dict of
    {id: status} (unlisted points pass), or an exception to raise."""
    calls = iter(answers)

    def review(parts, context):
        answer = next(calls)
        if isinstance(answer, Exception):
            raise answer
        ids = repeat.point_ids(parts)
        return [{"id": i, "status": answer.get(i, "pass"), "explanation": "x", "requested_change": ""} for i in ids], model

    return review


class NoRealCalls(unittest.TestCase):
    def setUp(self):
        guard = mock.patch.object(claude_review.anthropic, "Anthropic", side_effect=AssertionError("a test tried to call the real API"))
        guard.start()
        self.addCleanup(guard.stop)
        quiet = mock.patch("sys.stderr", io.StringIO())
        quiet.start()
        self.addCleanup(quiet.stop)


class RepeatTest(NoRealCalls):
    # AI-written: only the points Claude judges are sent, the same parts and
    # context on every run.
    def test_sends_only_llm_points_every_run(self):
        seen = []

        def review(parts, context):
            seen.append((repeat.point_ids(parts), context))
            return fake_review({})(parts, context)

        repeat.repeat(LLM_PARTS, CONTEXT, 3, review)
        self.assertEqual(len(seen), 3)
        for ids, context in seen:
            self.assertEqual(ids, IDS)
            self.assertIs(context, CONTEXT)
        for scripted in script_checks_ids():
            self.assertNotIn(scripted, IDS)

    # AI-written: a failed run is recorded and the other runs still happen.
    def test_failed_run_is_recorded_and_others_continue(self):
        review = fake_review({}, claude_review.ReviewError("cut off"), ValueError("bad JSON"))
        runs = repeat.repeat(LLM_PARTS, CONTEXT, 3, review)
        self.assertIn("results", runs[0])
        self.assertEqual(runs[1], {"error": "ReviewError: cut off"})
        self.assertEqual(runs[2], {"error": "ValueError: bad JSON"})


def script_checks_ids():
    import script_checks

    return list(script_checks.CHECKS)


class SummarizeTest(NoRealCalls):
    def rows(self, *answers, expected=None):
        runs = repeat.repeat(LLM_PARTS, CONTEXT, len(answers), fake_review(*answers))
        return {row["id"]: row for row in repeat.summarize(IDS, runs, expected or {})}, runs

    # AI-written: 3/3 is stable, 2/3 is not.
    def test_stable_and_unstable_points(self):
        rows, _ = self.rows({}, {"summary_what": "fail"}, {})
        self.assertTrue(rows["problem_stated"]["stable"])
        self.assertEqual(rows["problem_stated"]["agree"], 3)
        self.assertFalse(rows["summary_what"]["stable"])
        self.assertEqual(rows["summary_what"]["statuses"], ["pass", "fail", "pass"])
        self.assertEqual(rows["summary_what"]["agree"], 2)

    # AI-written: a failed run makes every point unstable, even when the runs
    # that answered agree, so 2 answers out of 3 never count as 3/3.
    def test_failed_run_is_not_stable(self):
        rows, _ = self.rows({}, claude_review.ReviewError("x"), {})
        row = rows["problem_stated"]
        self.assertEqual(row["statuses"], ["pass", repeat.ERROR, "pass"])
        self.assertEqual(row["agree"], 2)
        self.assertFalse(row["stable"])

    # AI-written: "correct" counts the runs that gave the expected status, and
    # is None for a point with no expected status.
    def test_counts_runs_matching_expected(self):
        rows, _ = self.rows({"problem_stated": "fail"}, {}, {}, expected={"problem_stated": "fail", "summary_what": "pass"})
        self.assertEqual(rows["problem_stated"]["correct"], 1)
        self.assertEqual(rows["summary_what"]["correct"], 3)
        self.assertIsNone(rows["verification_tests"]["correct"])


class RenderTest(NoRealCalls):
    def table(self, *answers, expected=None, model="claude-opus-5-5"):
        runs = repeat.repeat(LLM_PARTS, CONTEXT, len(answers), fake_review(*answers, model=model))
        rows = repeat.summarize(IDS, runs, expected or {})
        return repeat.render("user/demo#7", runs, rows), runs, rows

    def line(self, text, point_id):
        return next(line for line in text.splitlines() if line.strip().startswith(point_id + " "))

    # AI-written: an unstable point is marked with "←", a stable one isn't.
    def test_marks_unstable_points(self):
        text, _, _ = self.table({}, {"summary_what": "fail"}, {})
        self.assertIn("2/3 ←", self.line(text, "summary_what"))
        self.assertIn("3/3", self.line(text, "problem_stated"))
        self.assertNotIn("←", self.line(text, "problem_stated"))

    # AI-written: a point whose runs don't all match the expected status gets "✗".
    def test_marks_mismatch_with_expected(self):
        text, _, _ = self.table({}, {}, {}, expected={"problem_stated": "fail", "summary_what": "pass"})
        self.assertIn("fail 0/3 ✗", self.line(text, "problem_stated"))
        self.assertIn("pass 3/3", self.line(text, "summary_what"))
        self.assertNotIn("✗", self.line(text, "summary_what"))

    # AI-written: runs answered by different models (a fallback) are flagged.
    def test_flags_different_models(self):
        runs = [
            {"model": "claude-opus-5-5", "results": {i: {"status": "pass", "explanation": ""} for i in IDS}},
            {"model": "fallback-model", "results": {i: {"status": "pass", "explanation": ""} for i in IDS}},
        ]
        text = repeat.render("user/demo#7", runs, repeat.summarize(IDS, runs, {}))
        self.assertIn("different models", text)

    # AI-written: the overall table counts stable points per point over PRs.
    def test_overall_counts_per_point(self):
        _, _, stable = self.table({}, {}, {})
        _, _, unstable = self.table({}, {"summary_what": "fail"}, {})
        text = repeat.render_overall({"a#1": stable, "b#2": unstable})
        self.assertIn("1/2", self.line(text, "summary_what"))
        self.assertIn("2/2", self.line(text, "problem_stated"))
        self.assertIn(f"Stable: {2 * len(IDS) - 1}/{2 * len(IDS)}", text)


class MainTest(NoRealCalls):
    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.context_file = self.tmp / "ctx.json"
        review_cli.save_context(CONTEXT, self.context_file)
        self.expected = self.tmp / "expected.json"
        self.expected.write_text(json.dumps({"user/demo#7": {}}), encoding="utf-8")

    def main(self, *argv, review=None):
        out = io.StringIO()
        with redirect_stdout(out):
            repeat.main([*argv, "--expected", str(self.expected), str(self.context_file)], review=review)
        return out.getvalue()

    # AI-written: without --run, nothing calls Claude, not even with a key set,
    # and the plan says how many calls --run would make.
    def test_without_run_makes_no_calls(self):
        with mock.patch.object(claude_review, "review", side_effect=AssertionError("called Claude")), mock.patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"}):
            text = self.main("--runs", "3")
        self.assertIn("--run would make 3 Claude calls (1 contexts × 3 runs)", text)
        self.assertIn("No Claude calls were made", text)

    # AI-written: --run without an API key stops before any call.
    def test_run_without_key_stops(self):
        with mock.patch.dict("os.environ", {}, clear=True), self.assertRaises(SystemExit) as stop:
            self.main("--run")
        self.assertIn("ANTHROPIC_API_KEY", str(stop.exception))

    # AI-written: --run writes every run's raw results, the rows and the
    # criteria hash to --out, and prints the tables.
    def test_run_writes_results(self):
        out = self.tmp / "out" / "after.json"
        text = self.main("--run", "--runs", "2", "--label", "after", "--out", str(out), review=fake_review({}, {"summary_what": "fail"}))
        self.assertIn("user/demo#7 · 2 runs", text)
        self.assertIn("Per point over 1 PRs", text)
        saved = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(saved["label"], "after")
        self.assertEqual(len(saved["criteria_sha256"]), 64)
        pr = saved["prs"]["user/demo#7"]
        self.assertEqual(len(pr["runs"]), 2)
        self.assertEqual(next(r for r in pr["rows"] if r["id"] == "summary_what")["statuses"], ["pass", "fail"])


class AvailableContextsTest(NoRealCalls):
    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        (self.tmp / "contexts").mkdir()
        review_cli.save_context(CONTEXT, self.tmp / "contexts" / "pr7.json")
        self.expected = self.tmp / "expected.json"
        self.expected.write_text(json.dumps({"user/demo#7": {}, "user/demo#8": {}}), encoding="utf-8")
        folder = mock.patch.object(repeat, "CONTEXTS", self.tmp / "contexts")
        folder.start()
        self.addCleanup(folder.stop)

    def main(self, *argv, review=None):
        out = io.StringIO()
        with redirect_stdout(out):
            repeat.main([*argv, "--expected", str(self.expected)], review=review)
        return out.getvalue()

    # AI-written: with no file arguments, only the contexts present in the
    # folder are run, and the PR without one is named as skipped.
    def test_runs_only_present_contexts(self):
        text = self.main("--runs", "3")
        self.assertIn("user/demo#7 (pr7.json)", text)
        self.assertIn("Skipped, no context file: user/demo#8", text)
        self.assertNotIn("Skipped, no context file: user/demo#7", text)
        self.assertIn("3 Claude calls (1 contexts × 3 runs)", text)

    # AI-written: --run also reviews only the present context.
    def test_run_reviews_only_present_contexts(self):
        out = self.tmp / "out.json"
        self.main("--run", "--runs", "1", "--out", str(out), review=fake_review({}))
        self.assertEqual(list(json.loads(out.read_text(encoding="utf-8"))["prs"]), ["user/demo#7"])

    # AI-written: a context for a PR that isn't in expected.json is ignored,
    # also when it is named on the command line.
    def test_context_not_in_expected_is_ignored(self):
        other = self.tmp / "contexts" / "pr9.json"
        review_cli.save_context({**CONTEXT, "pr_number": 9}, other)
        for argv in ((), (str(other), str(self.tmp / "contexts" / "pr7.json"))):
            with self.subTest(argv=argv):
                text = self.main("--runs", "3", *argv)
                self.assertIn("Ignored, not in expected.json: user/demo#9 (pr9.json)", text)
                self.assertNotIn("user/demo#9 (pr9.json): 9 points", text)
                self.assertIn("3 Claude calls (1 contexts × 3 runs)", text)

    # AI-written: when no context is for a PR in expected.json, nothing runs.
    def test_only_unknown_contexts_stops(self):
        (self.tmp / "contexts" / "pr7.json").unlink()
        review_cli.save_context({**CONTEXT, "pr_number": 9}, self.tmp / "contexts" / "pr9.json")
        with self.assertRaises(SystemExit) as stop:
            self.main("--run", review=fake_review({}))
        self.assertIn("None of the context files is for a PR", str(stop.exception))

    # AI-written: an empty folder stops with a hint where to get the contexts.
    def test_no_contexts_stops_with_hint(self):
        (self.tmp / "contexts" / "pr7.json").unlink()
        with self.assertRaises(SystemExit) as stop:
            self.main()
        self.assertIn("Google Drive", str(stop.exception))


class ExpectedFileTest(unittest.TestCase):
    # AI-written: expected.json names a status for every point Claude judges,
    # for the 4 sample PRs, and each status is one Claude can return. The
    # context files may be missing, since they are kept on Google Drive.
    def test_expected_covers_every_llm_point(self):
        expected = repeat.load_expected(repeat.DEFAULT_EXPECTED)
        self.assertEqual(sorted(expected), [f"stickerdaniel/linkedin-mcp-server#{n}" for n in (1415, 1521, 1526, 1561)])
        llm_ids = [i for i in repeat.point_ids(PARTS) if i not in script_checks_ids()]
        for key, statuses in expected.items():
            with self.subTest(pr=key):
                self.assertEqual(sorted(statuses), sorted(llm_ids))
                self.assertLessEqual(set(statuses.values()), {"pass", "fail", "n/a"})


if __name__ == "__main__":
    unittest.main()
