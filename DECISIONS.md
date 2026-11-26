# Decisions Log

## 2026-09-24 — Initial code steward
**What:** Daniel Sticker (stickerdaniel) is the initial code steward for the team.
**Why:** Volunteered for the first rotation.

## 2026-11-27 — AI usage guidelines match how we worked in Phase 2
**What:** Dropped "AI reviews every PR before the human review" and the personal prompt and collaboration logs. The steward reviews every PR, and AI review is optional. The PR's AI assistance section, PR comments and the steward entries here replace the logs.
**Why:** In Phase 2 none of us kept the logs, and no AI review ran before the steward's review. Guidelines we don't follow don't help anyone.
**Alternative rejected:** Keep the Week 3 rules and start following them.
**Led by:** UGisBusy

## 2026-11-27 — CLAUDE.md is for coding agents, the bot's prompt has its own card
**What:** The root CLAUDE.md tells coding agents how to work in this repo. The bot's system prompt stays in `bot/claude_review.py` and is documented in `docs/prompt-card.md`.
**Why:** Claude Code reads a root CLAUDE.md as instructions for itself, and the bot sends it to Claude as this repo's agent guide. Putting the bot's prompt there would mix two audiences. Keeping one copy of the prompt, in the code, means it can't drift.
**Alternative rejected:** A `bot/CLAUDE.md` holding a copy of the system prompt.
**Led by:** UGisBusy
