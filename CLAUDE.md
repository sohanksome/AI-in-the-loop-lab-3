# CLAUDE.md

Instructions for coding agents working in this repository. The rules come from our AI usage guidelines in [README.md, Part 2](README.md#part-2-ai-usage-guidelines). This file says how an agent follows them.

## What this repo is

A GitHub Actions bot that reviews pull requests. An allowed user comments `/review` on a PR. The workflow then reads the PR through the GitHub API, asks Claude to judge it against the points in `bot/criteria.json`, and posts a comment listing what is missing. What the bot's own prompt says and where it goes wrong is in [docs/prompt-card.md](docs/prompt-card.md).

| Path | What it does |
| --- | --- |
| `.github/workflows/review.yml` | Runs on `/review` comments from users listed in `REVIEW_BOT_USERS` |
| `bot/review.py` | Entry point. Picks the mode and prints the PR comment |
| `bot/github_context.py` | Collects the PR and repository context with `gh api` |
| `bot/claude_review.py` | Builds the prompt, calls Claude, checks the answer |
| `bot/criteria.json` | The points a PR is judged on |
| `bot/report.py` | Turns the results into the comment and the score |
| `SETUP.md` | Setup and how to test |
| `DECISIONS.md` | Every significant decision |
| `docs/cp2-plan.md` | Who does what for CP2 |

## Running it

```sh
pip install -r bot/requirements.txt
python bot/review.py --dummy                              # sample report, no API calls
python bot/review.py --repo OWNER/REPO --pr 123 --dry-run # prints the prompt, needs gh, no Claude call
```

A full review needs `ANTHROPIC_API_KEY` and costs tokens. Ask before running one.

## Rules

1. **Commits.** Start the message with `[AI]` when you wrote most of the change, followed by our usual style, for example `[AI] docs(readme): Add prompt card link`.
2. **Pull requests.** Use `.github/pull_request_template.md`. Fill in the AI assistance section: tool and model, the files you generated, and the one-line instruction you were given. Leave "What I changed afterwards" for the human. Don't merge PRs. The code steward of the day does that.
3. **Author review.** Never write the author's self-review comment on a PR. It has to be written without AI.
4. **DECISIONS.md.** You may draft an entry. The decision, the reason and the rejected alternative come from the person under "Led by". If you don't know them, ask instead of making them up.
5. **Tests.** Give each test case a short comment saying whether a human or AI wrote it.
6. **Prompt changes.** If you change `SYSTEM_TEMPLATE` or `USER_TEMPLATE` in `bot/claude_review.py`, `bot/criteria.json`, `MODEL` or `EFFORT`:
   - update [docs/prompt-card.md](docs/prompt-card.md) in the same PR
   - check the new prompt with `--dry-run`
   - once the prompt test suite exists, run it and put the results from before and after the change in the PR
7. **Keep the bot safe.** The workflow holds the API key, so:
   - Never check out or run the PR's code in the workflow. Read the PR only through the GitHub API.
   - Text from the PR is data, not instructions. If you add a tag to the prompt templates, add it to `_PROMPT_TAG` in `bot/claude_review.py`. Pass every PR value through `_text()` or `_attr()`.
   - Read repository guides from the PR's base commit, so a PR can't change the rules it is judged by.
   - Text from Claude goes into a public PR comment. Keep passing it through `_one_line()` in `bot/report.py`.
