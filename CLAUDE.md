# CLAUDE.md

Instructions for coding agents working in this repository.

## Working with agents

| Topic | Rule |
| --- | --- |
| **Commits** | Write the subject as `type(scope): Capitalized imperative`, for example `feat(review): Add a pass/fail rule to each criterion`. When you wrote most of the change, end the message with a `Co-Authored-By:` line naming the model, for example `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. |
| **Pull requests** | Use `.github/pull_request_template.md`. Fill in the AI assistance section: tool and model, the files you generated, and the one-line instruction you were given. Leave "What I changed afterwards" for the human. |
| **Author review** | Never write the author's self-review comment on a PR. It has to be written without AI. |
| **DECISIONS.md** | You (AI) may draft an entry. The decision, the reason and the rejected alternative come from the person under "Led by". A human finalizes them later. |
| **Tests** | Give each test case a short comment saying whether a human or AI wrote it. |
| **Review bot prompt** | The review bot's prompt lives in `bot/claude_review.py` and `bot/criteria.json`. See [docs/prompt-card.md](docs/prompt-card.md). |

