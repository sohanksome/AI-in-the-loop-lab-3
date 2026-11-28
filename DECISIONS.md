# Decisions Log

## 2026-09-24 — Initial code steward
**What:** Daniel Sticker (stickerdaniel) is the initial code steward for the team.\
**Why:** Volunteered for the first rotation.

## 2026-11-21 — GH action to activate bot review
**Why:** No backend required, easy to setup\
**Alternative rejected:** Host backend sever (python Fast API or some JS stuff)\
**Led by:** UGisBusy

## 2026-11-21 — Only allowed user can request bot review
**Why:** Prevent burning tokens from spamming reviews\
**Alternative rejected:** auto-review on every PR push, or letting anyone (including the pr author) trigger it\
**Led by:** UGisBusy

## 2026-11-21 — Store API key in the GH repo secret
**Why:** To make GH action able to access it, though this introduce some issues:
1. Everyone with write access can read it
2. Any PR code that runs in the same job could read and leak the key, so the job never runs PR code
3. Review bot users can still spam requests

**Alternative rejected:** avoid this if we're using backend sever approach\
**Led by:** UGisBusy

## 2026-11-27 — CP2 code steward rotation
**What:** Daniel Sticker (stickerdaniel) is the code steward on Thu 26 Nov, UG on Fri 27, sohanksome on Sat 28 morning and heyvrann on Sat 28 afternoon. The steward reviews and merges the PRs that are ready during the slot, never their own.\
**Why:** The whole team planned it beforehand. For CP2, each of us needs a steward turn recorded in `DECISIONS.md`, and if we merge as we go, merge day stays small.\
**Alternative rejected:** Merging everything on merge day.\
**Led by:** Daniel Sticker (stickerdaniel), proposed in the CP2 plan ([#16](https://github.com/sohanksome/AI-in-the-loop-lab-3/pull/16))

## 2026-11-27 — CP2 code steward rotation 1 review status
**What:**
1. **C1**: approved and merged
2. **D2**: approved and merged

**Led by:** Daniel Sticker (stickerdaniel)

## 2026-11-27 — CP2 code steward rotation 2 review status
**What:**
1. **C2**: approved and merged
2. **C3**: approved and merged
3. **C4**: TBD
4. **C7**: TBD

**Led by:** UG (UGisBusy)

## 2026-11-28 — CP2 code steward rotation 3 review status
**What:**
1. **C6**: TBD
2. **D1**: approved and merged
3. **C8**: TBD
4. **D4**: TBD

**Led by:** sohanksome

## 2026-11-26 — Finish the current prototype for CP2, sandbox after
**What:** We finish the review prototype from [#9](https://github.com/sohanksome/AI-in-the-loop-lab-3/pull/9) for CP2 and build the sandbox reviewer after CP2.\
**Why:** We liked the sandbox idea, because the current approach doesn't scale well. The prototype from [#9](https://github.com/sohanksome/AI-in-the-loop-lab-3/pull/9) already exists, and CP2 is due Sunday.\
**Alternative rejected:** Building the sandbox reviewer before CP2.\
**Led by:** Daniel proposed the sandbox, and all four of us decided in the meeting on 26 Nov.

## 2026-11-28 — Price each review from a hard-coded price table (C7)
**What:** `report.json` gets a `usage` field with the review's input, output and cache tokens and its cost in USD. `bot/cost.py` computes the USD from the token counts the API returns and a price table copied from Anthropic's pricing page, with the date it was checked. With server-side fallbacks, every attempt is added up at its own model's price.\
**Why:** Issue [#12](https://github.com/sohanksome/PR-message-quality-assurance-bot/issues/12) needs the cost per review on PRs of different sizes before we cut anything, and the Action only has a normal API key. A model without a listed price records `usd: null` instead of failing the review.\
**Alternative rejected:** Reading the cost from the Usage and Cost API, which needs an admin key and reports per day, not per request; estimating from prompt characters, which misses output and thinking tokens.\
**Led by:** heyvrann
