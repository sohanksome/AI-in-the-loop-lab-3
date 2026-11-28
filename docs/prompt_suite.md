# Prompt suite

CP2 task **C5**, Group 24. Ten frozen pull requests with expected results, a runner that lists where the bot disagrees with them, and one recorded round of fail, fix and re-run.

## What the suite is

Each case is a pull request from [linkedin-mcp-server](https://github.com/stickerdaniel/linkedin-mcp-server), saved once with `review.py --save-context` (C4), so it always gives the bot the same prompt and needs no GitHub calls. `bot/evaluation/expected.json` holds, for each case, the status we expect for each of the 9 points Claude judges. The 3 points checked in Python (C3) are left out, because they give the same answer every time.

| PR | Why it's in the suite |
| --- | --- |
| [#1415](https://github.com/stickerdaniel/linkedin-mcp-server/pull/1415) | Maintainer README fix with before and after screenshots, no Verification section |
| [#1480](https://github.com/stickerdaniel/linkedin-mcp-server/pull/1480) | Contributor code PR that left the template untouched |
| [#1511](https://github.com/stickerdaniel/linkedin-mcp-server/pull/1511) | Very long description; the issues it names are other PRs, mentioned for comparison |
| [#1521](https://github.com/stickerdaniel/linkedin-mcp-server/pull/1521) | Complete contributor feature that also changes `AGENTS.md` |
| [#1523](https://github.com/stickerdaniel/linkedin-mcp-server/pull/1523) | Complete contributor fix that links its issue with "Refs" |
| [#1526](https://github.com/stickerdaniel/linkedin-mcp-server/pull/1526) | Complete contributor fix |
| [#1530](https://github.com/stickerdaniel/linkedin-mcp-server/pull/1530) | Complete contributor feature that closes its issue |
| [#1548](https://github.com/stickerdaniel/linkedin-mcp-server/pull/1548) | Renovate bot dependency bump with no template sections |
| [#1557](https://github.com/stickerdaniel/linkedin-mcp-server/pull/1557) | Maintainer test fix with Problem and Solution sections, no issue |
| [#1561](https://github.com/stickerdaniel/linkedin-mcp-server/pull/1561) | Closed contributor PR with one-line sections and no prompt |

UG chose #1415, #1521, #1526 and #1561 for C6; C5 adds the other six. The saved contexts stay out of git and are shared on the team's Google Drive (see `DECISIONS.md`, 2026-11-27).

## How to run it

Put the context files in `bot/evaluation/contexts/`, then:

```
python bot/evaluation/repeat.py --runs 1                       # plan only, free
python bot/evaluation/repeat.py --run --runs 1 --label suite   # one review per PR
```

The runner prints a table per PR and marks every point that disagrees with `expected.json` with ✗, then a table that counts mismatches per point. One run of all 10 PRs is about 725k input tokens, about $3 with `claude-opus-5-5`. The plan's estimate of 455k is too low, because it counts 4 characters per token.

## Round 1: the suite as C6 left it

28 November 2026, one review per PR, `claude-opus-5-5`, effort `medium`. The first attempt ran out of API credit after 7 PRs; the other 3 ran later the same day on the same rules (same `criteria.json` checksum).

**87 of 90 points matched.** Three mismatches, on two PRs:

| PR | Point | Expected | Bot | Bot's reason |
| --- | --- | --- | --- | --- |
| #1415 | `problem_impact` | pass | fail | "The description says the row wrapped, but not who runs into this or what goes wrong for readers because of it." |
| #1548 | `problem_stated` | fail | pass | "The release notes describe the old behavior: a missing effort used to fail with a pointer to `(effort unknown)`, which v4.1.1 replaces with a request for the reasoning setting." |
| #1548 | `problem_impact` | n/a | pass | "The release notes say the attribution check fails on a missing effort and that the message contributors see changes. This affects PR authors whose attribution line lacks an effort." |

#1415 `problem_impact` is the point C6 already found unstable; UG kept its rule on purpose. The two #1548 mismatches are one disagreement: `problem_impact` is n/a only when `problem_stated` fails. The rule didn't say whether release notes copied from a dependency count as stating the project's problem, and Claude counted them.

## The fix

We decided they don't count: Renovate copies the dependency's release notes, which describe the dependency, not a problem in this project. One sentence was added to the end of `problem_stated`'s `fail_if` condition in `bot/criteria.json`:

> Release notes or a changelog copied from a dependency don't count either: they describe the dependency, not what was wrong in this project.

`expected.json` was not changed.

## Round 2: after the fix

Same day, same settings, all 10 PRs again, because the rule applies to every PR.

**88 of 90 points matched.**

| PR | Point | Expected | Round 1 | Round 2 |
| --- | --- | --- | --- | --- |
| #1548 | `problem_stated` | fail | pass ✗ | **fail** |
| #1548 | `problem_impact` | n/a | pass ✗ | **n/a** |
| #1415 | `problem_impact` | pass | fail ✗ | pass |
| #1521 | `problem_stated` | pass | pass | **fail ✗** |
| #1521 | `problem_impact` | pass | pass | **n/a ✗** |

The other 85 points gave the same status in both rounds.

- **#1548 is fixed**, which is the fail, fix and re-run this task asked for.
- **#1415** flipped back to pass. Our sentence is about dependency release notes and has nothing to do with this PR, so this is the known instability, not the fix.
- **#1521 is new.** The bot said: "The Summary only describes what `start` adds and how it behaves. No sentence says that, before this change, a search cut short by `max_pages` or the time budget could only be rerun from the first result." That reason comes from the older part of the rule ("a description that only lists what the PR adds"), not the new sentence. But "don't count **either**" may make the whole condition read stricter, and C6's runs passed this point 3 out of 3 times before the change.

## Open: is #1521 noise or caused by the fix?

One run can't tell, and we did not re-check it for CP2. #1521 stays an open question, with a known way to settle it: review it three more times on the fixed rules (about $0.90).

```
python bot/evaluation/repeat.py --run --runs 3 --label pr1521-recheck bot/evaluation/contexts/pr1521.json
```

- If it passes in 2 or 3 runs, it was a flip like #1415, and the fix stays as it is.
- If it fails in all 3, the sentence made the rule stricter. We would then write it as a separate sentence without "either", and re-run #1521 and #1548.

## Cost

| Run | PRs | Input tokens | Output tokens | About |
| --- | --- | --- | --- | --- |
| Round 1, first 7 | 7 | 543,450 | 6,598 | $2.30 |
| Round 1, last 3 | 3 | 180,542 | 3,761 | $0.80 |
| Round 2 | 10 | 724,382 | 10,214 | $3.10 |
| **Total** | | | | **$6.20** |

Prices are `claude-opus-5-5` list prices, $4 per million input tokens and $20 per million output tokens.

## Limits

- **One run per PR per round.** A point that flips now and then, like #1415, can look fixed or broken by chance. C6's repeat runs measure that; this suite only checks against expected results.
- **The expected results are ours.** They follow C6's rules as we read them, so the suite measures agreement with our reading, not with an outside judge.
- **Ten PRs from one repository** cover the cases we found, not every kind of PR.
