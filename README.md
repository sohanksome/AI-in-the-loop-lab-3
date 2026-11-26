# PR Message Quality Assurance Bot

<p align="left">
  <a href="https://csic30216-fall26.denniswang.net/"><img src="https://img.shields.io/badge/NYCU_AI--in--the--Loop-Fall_2026_%C2%B7_Group_24-0969da" alt="NYCU AI-in-the-Loop, Fall 2026, Group 24"></a>
  <a href="https://github.com/sohanksome"><img src="https://img.shields.io/badge/sohanksome-24292f?logo=github" alt="sohanksome"></a>
  <a href="https://github.com/heyvrann"><img src="https://img.shields.io/badge/heyvrann-24292f?logo=github" alt="heyvrann"></a>
  <a href="https://github.com/UGisBusy"><img src="https://img.shields.io/badge/UGisBusy-24292f?logo=github" alt="UGisBusy"></a>
  <a href="https://github.com/stickerdaniel"><img src="https://img.shields.io/badge/stickerdaniel-24292f?logo=github" alt="stickerdaniel"></a>
</p>

This project is a bot that reviews incoming pull requests against a project's quality bar and keeps asking for changes until a PR meets it. Everything a script can check runs as a CI check. The bot uses an LLM for what a script can't judge, such as whether the description explains why a change is needed or whether the tests cover the changed behavior. The bot plays bad cop and pushes back whenever a quality criterion is missing. The maintainer plays good cop, discusses ideas, thanks contributors and merges their work. A dashboard that lists open PRs ready for human review may follow later and is not part of the evaluation.

## Part 2: AI usage guidelines

Updated for CP2 from our Week 3 draft, to match how we actually worked in Phase 2. [What changed since Week 3](#what-changed-since-week-3) lists each change and why.

### Tools and what we use them for

Each of us picks the model and coding-agent harness that fits the task, since new models come out during the semester. Every PR fills in the "AI assistance" section of the PR template: the model, the files it generated, and what we changed. A PR with this section empty isn't merged. Current defaults:

- We use **Claude models**, ideally Opus or Fable, to drive the session and write code and documentation. The final architecture call stays with us. They write well and keep changes in scope. Sonnet is cheaper, but its output is noticeably weaker.
- We use **GPT models**, ideally Sol or Astra, for reviews and codebase analysis, because they are thorough. Their findings inform the merge decision but don't make it. They also write decent code, but they often investigate far more than the task needs and want to test and check everything.
- We use **GitHub Copilot** to autocomplete code and review PRs.
- The code steward of the day reviews and merges every PR, never its author. An AI review from Copilot or a GPT model is optional input for the steward, not a step every PR goes through.

### How we document AI interactions

- **AI commits:** every commit where AI wrote most of the change starts with `[AI]`, for example `[AI] add dry-run and dummy modes`.
- **Prompts:** the "Instruction given" line in the PR's AI assistance section records the instruction that shaped the change, and "What I changed afterwards" records what we kept or changed. Quick syntax or debugging questions don't need a mention.
- **Reviews and handoffs:** review conversations happen in PR comments. Each code steward's slot gets a DECISIONS.md entry with a short handoff note, so it's clear later who reviewed and merged what.
- **Coding agents:** [CLAUDE.md](CLAUDE.md) turns these rules into instructions for coding agents. Claude Code reads it on its own. With another harness, point the agent at it.
- **The bot's prompt:** a PR that changes the bot's prompt, `bot/criteria.json` or the model updates the [prompt card](docs/prompt-card.md) in the same PR. Once the prompt test suite exists, the PR also shows its results before and after the change.
- **DECISIONS.md:** every significant decision gets an entry, including ones that came out of AI output. An agent can write it up, but the decision, the reason and the rejected alternative come from the person under "Led by", who checks the entry before merge. [DECISIONS.md →](DECISIONS.md)
- **Tests:** a short comment on each test case says whether a human or AI wrote it.

### How we handle disagreements about AI output

- If we disagree on whether AI-generated code is ready to merge, the code steward decides and adds one sentence on why to DECISIONS.md.
- Code is ready to merge when it passes the test suite, follows the PR template, and the author has reviewed it once and left a short comment that sums up the change, written without AI assistance.
- For style questions we go with our linter and formatter configuration.

### What changed since Week 3

| Week 3 draft | Now | Why |
| --- | --- | --- |
| Every PR records which model did what. | The PR's AI assistance section names the model, the files it generated, the instruction and what we changed. If it's empty, the PR isn't merged. | Team 12's Week 12 review ([#10](https://github.com/sohanksome/AI-in-the-loop-lab-3/issues/10)) couldn't tell from PR #9's description what the AI did. |
| Ready to merge when someone other than the author can explain it. | The author reviews the PR once and leaves a short summary comment, written without AI. | PR #9 is mostly AI-generated, and nothing in it showed the author could explain it without AI. |
| The last line of every PR body names each model and harness. | Commits where AI wrote most of the change start with `[AI]`. | In PR #9 the `[AI]` tags were the only place that showed which parts the AI wrote. |
| AI reviews every PR before the human review. | The steward reviews every PR. AI review is optional. | In Phase 2 no AI review ran before the steward's review. |
| Each of us keeps a prompt engineering log and a collaboration log. | The PR's AI assistance section, PR comments and the steward entries in DECISIONS.md cover this. | None of us kept the logs. The PR is where a reviewer looks anyway. |
| (new) | CLAUDE.md for coding agents, and a prompt card for the bot. | CP2 asks for both. |

## Part 3: Evaluation plan (draft)

### Problem grounding

- **Who has the problem:** maintainers of open-source projects that get more pull requests than they can review, and the contributors whose PRs wait. We test on [linkedin-mcp-server](https://github.com/stickerdaniel/linkedin-mcp-server), which a student on our team maintains alone.
- **What they do today:** an AI reviewer already comments on new PRs, but the maintainer still decides alone what has to change. When a PR needs work, it's often quicker for the maintainer to push the missing commits than to explain what's missing. That happened in 29 of the 53 contributor PRs merged so far. The contributor learns less for the next PR, and the maintainer does thinking the contributor, who knows the feature best, could have done. PRs the maintainer has no time for wait without a maintainer response. On 24 September 2026, 80 contributor PRs were open, with a median age of about 60 days.
- **What would change:** when the bot asks for something, the contributor pushes the fix themselves. The maintainer pushes fewer commits to other people's PRs and spends review time on the ideas in them.

### Evaluation plan

- **Success definition:** the tool works if contributors resolve most of the bot's requests with their own commits, and if fewer merged PRs need maintainer commits than before. A human stays in the loop. The bot only advises, the contributor decides how to respond, and the maintainer can overrule the bot and decides on the merge. Contributors also have to find the bot's comments worth the interruption, and we count how many bot requests the maintainer judges wrong.
- **Target users:** contributors to open-source repositories with more PR traffic than the maintainers can handle. Our test group is the people who open PRs on linkedin-mcp-server during the semester. The bot's comment invites them to a short call or a written Q&A. If too few reply, we also ask contributors from the baseline period.
- **Method:** structured observation of PR activity with a fixed coding sheet, plus brief interviews. The baseline is fixed now: all 53 contributor PRs merged by 24 September 2026. A PR counts as needing maintainer work if it has at least one non-merge commit by the maintainer. The bot runs on new PRs from week 10. Interim results go into CP2 in week 12, and observation continues until week 14.
- **Minimum evidence threshold:** the bot has reviewed at least 20 contributor PRs and at least 10 of them are merged or closed, contributors resolved at least half of the bot's requests with their own commits, the share of merged PRs with maintainer commits is below 40% (baseline 29 of 53, 55%), and at least 3 contributors from outside our team told us in an interview what the bot changed for them.
- **Known limits:** the maintainer is on our team and controls one of the metrics, Greptile keeps reviewing alongside our bot, the sample is small, and the maintainer often merges in batches.
