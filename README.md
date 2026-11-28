# PR Message Quality Assurance Bot

<p align="left">
  <a href="https://csic30216-fall26.denniswang.net/"><img src="https://img.shields.io/badge/NYCU_AI--in--the--Loop-Fall_2026_%C2%B7_Group_24-0969da" alt="NYCU AI-in-the-Loop, Fall 2026, Group 24"></a>
  <a href="https://github.com/sohanksome"><img src="https://img.shields.io/badge/sohanksome-24292f?logo=github" alt="sohanksome"></a>
  <a href="https://github.com/heyvrann"><img src="https://img.shields.io/badge/heyvrann-24292f?logo=github" alt="heyvrann"></a>
  <a href="https://github.com/UGisBusy"><img src="https://img.shields.io/badge/UGisBusy-24292f?logo=github" alt="UGisBusy"></a>
  <a href="https://github.com/stickerdaniel"><img src="https://img.shields.io/badge/stickerdaniel-24292f?logo=github" alt="stickerdaniel"></a>
</p>

This project is a bot that reviews incoming pull requests against a project's quality bar and keeps asking for changes until a PR meets it. Everything a script can check runs as a CI check. The bot uses an LLM for what a script can't judge, such as whether the description explains why a change is needed or whether the tests cover the changed behavior. The bot plays bad cop and pushes back whenever a quality criterion is missing. The maintainer plays good cop, discusses ideas, thanks contributors and merges their work. A dashboard that lists open PRs ready for human review may follow later and is not part of the evaluation.

## CP2 progress

All our CP2 tasks from [the CP2 plan](docs/cp2-plan.md), where the done criteria live. When your PR finishes a task, tick its row in that PR. Due Sun 29 Nov, 23:59 Taipei.

**IDs:** C = code PR (each of us needs 2 merged), D = doc for the CP2 zip, S = team session or process step.

**Reviewer:** whoever is steward when the PR is ready reviews and merges it, never the author. Slots: Daniel Thu, UG Fri, sohanksome Sat morning, heyvrann Sat afternoon.

**Needs:** start a task once these are merged. C1 blocks most of them, so we merge it first.

**Status:** ⬜ open, ✓ with the PR link once merged.

| Due | Task | Owner | Reviewer | Needs | Status |
| --- | --- | --- | --- | --- | --- |
| 11/26 | **S1** Steward rotation in DECISIONS.md, each steward merges during their slot | All | - | - | ⬜ |
| 11/26 | **C1** Merge [#9](https://github.com/sohanksome/AI-in-the-loop-lab-3/pull/9) | UG | Daniel | - | ✓ |
| 11/26 | **C2** Reject repeated results for a point | Daniel | UG | C1 | ✓ |
| 11/27 | **C3** Check filled sections in Python | Daniel | UG | C1 | ✓ |
| 11/27 | **C4** `--save-context` and `--context-file`, [#23](https://github.com/sohanksome/PR-message-quality-assurance-bot/pull/23). | sohanksome | UG | C1 | ✓ |
| 11/27 | **C6** Pass/fail rule per criterion and 3x repeat runs, closes [#11](https://github.com/sohanksome/AI-in-the-loop-lab-3/issues/11) | UG | sohanksome | C4 | ⬜ |
| 11/27 | **C7** Tokens and cost in report.json, for [#12](https://github.com/sohanksome/AI-in-the-loop-lab-3/issues/12), [#27](https://github.com/sohanksome/PR-message-quality-assurance-bot/pull/27). | heyvrann | UG | C1 | ✓ |
| 11/27 | **D1** CLAUDE.md and prompt card | UG | sohanksome | - | ✓ |
| 11/27 | **D2** AI guidelines, merge [#18](https://github.com/sohanksome/AI-in-the-loop-lab-3/pull/18) | UG | Daniel | - | ✓ |
| 11/27 | **S2** Walking skeleton: merged PR link and docs/walking_skeleton.md | All | - | C1 | ⬜ |
| 11/28 | **C5** Prompt suite runner, 10 frozen PRs with expected results | sohanksome | heyvrann | C4 | ⬜ |
| 11/28 | **C8** Re-review updates the existing comment | heyvrann | sohanksome | C1 | ⬜ |
| 11/28 | **D3** Design rationale with 2 user tests outside the team | sohanksome | heyvrann | C1 | ⬜ |
| 11/28 | **D4** Interim evaluation report | heyvrann | sohanksome | C5, C6, C7 | ⬜ |
| 11/28 | **S3** Merge day at 14:00: merge or close what is still open, fresh clone | Steward | - | - | ⬜ |
| 11/29 | **S4** DECISIONS.md complete | All | - | - | ⬜ |
| 11/29 | **S5** Contributor graph, zip, E3 upload | Daniel | - | S3, S4 | ⬜ |

## AI usage guidelines

### Tools and what we use them for

Each of us picks the model and coding-agent harness that fits the task, since new models come out during the semester. Every PR records which model did what. Current defaults:

- We use **Claude models**, ideally Opus or Fable, to drive the session and write code and documentation. The final architecture call stays with us. They write well and keep changes in scope. Sonnet is cheaper, but its output is noticeably weaker.
- We use **GPT models**, ideally Sol or Astra, for reviews and codebase analysis, because they are thorough. Their findings inform the merge decision but don't make it. They also write decent code, but they often investigate far more than the task needs and want to test and check everything.
- We use **GitHub Copilot** to autocomplete code and review PRs.
- AI reviews every PR before the human review, and the current code steward approves and merges.

### How we document AI interactions

- **Commits:** subjects follow `type(scope): Capitalized imperative`. When AI wrote most of the change, the message ends with a `Co-Authored-By:` line naming the model.
- **Pull requests:** fill in the AI assistance section of the PR template: the tool and model, the files AI generated, and the instruction it was given. The author writes "What I changed afterwards" and the self-review comment without AI.
- **DECISIONS.md:** AI may draft an entry, but the decision, the reason and the rejected alternative come from the person under "Led by", who checks it before merge.
- **Tests:** a short comment on each test case says whether a human or AI wrote it.

Coding agents get the same rules in [CLAUDE.md](CLAUDE.md), so they follow them without being told each time.

### How we handle disagreements about AI output

- **Two humans check every PR**, however much of it AI wrote: the author, who summarizes the change in the PR, and the code steward, who reviews it. Together they decide whether it's ready to merge.
- **AI review comments are advice.** If the author thinks an AI reviewer is wrong, they reply on the PR saying why, and the steward decides whether it blocks the merge.
- **If we still disagree**, the code steward decides and adds one sentence on why to DECISIONS.md.
- **Ready to merge** means it passes the tests, follows the PR template, and someone other than the person who generated it can explain it.

## Evaluation plan (draft)

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
