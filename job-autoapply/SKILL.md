---
name: job-autoapply
description: AI job-application copilot that finds matching jobs and applies on the user's behalf across Naukri, LinkedIn Easy Apply, Instahyre, Wellfound, Cutshort, Hirist, Indeed and company career sites (Greenhouse, Lever, Ashby), using a locally saved profile built from their resume. Use this skill whenever the user wants to auto-apply, bulk-apply, "apply to jobs for me", run or schedule their job hunt, set up or update their job profile, answer screening questions from their resume, add target companies, or check application history — even if they just say "run my job hunt" or "apply to a few jobs today".
---

# Job Auto-Apply Copilot (v2)

End-to-end job-hunt autopilot: discover jobs cheaply (APIs first, browser last), score them against the candidate's real profile, apply truthfully, verify each submission, and log everything locally so nothing is applied to twice.

## Ground rules

These protect the candidate's accounts and reputation. They apply in every mode, including full autopilot.

1. **Never fabricate.** Every answer must trace to the resume or to something the user told you. If a question can't be answered truthfully, skip the job and queue the question (`pending_questions.json`). Never round experience up.
2. **Real browser for logged-in sites.** Naukri, LinkedIn, Instahyre, Wellfound, Cutshort, Hirist and Indeed are driven only through Claude in Chrome in the user's own session. No headless browsers, Playwright, proxies, extra accounts, CAPTCHA solvers or fingerprint tricks on those sites.
3. **Stop on pushback.** CAPTCHA, OTP, "unusual activity", daily-limit message, login wall, or restriction notice → stop that platform for the day, log it, continue with other platforms, and report it.
4. **Caps are hard.** `store.py today` gives remaining budget per platform; never exceed it. Script-enforced hard maximums exist per platform.
5. **LinkedIn ToS.** LinkedIn prohibits automation. Its default is `approve_each`; the user may choose otherwise only after `linkedin.tos_risk_acknowledged` is set true. Respect that choice.
6. **Supervised start.** On any platform, run in `approve_each` until `supervised_runs.<platform>` ≥ 2. After that, use the configured mode.

## Local data (`~/job-autoapply/`, via `scripts/store.py` only)

```
profile.json           candidate facts, prefs, exclusions, per-platform automation settings
answers.json           screening-question answer bank (grows every run)
applied.jsonl          every attempt: applied / skipped / skipped_question / failed / external
pending_questions.json questions you couldn't answer truthfully
targets.json           company career boards to watch [{ats, slug, company}]
jobs.jsonl             latest discovered jobs (normalized), overwritten each run
shortlist.json         prefiltered + scored jobs for this run
recipes.md             learned site quirks (selectors, flow changes) — read before each platform
resumes/               resume files
```

No filesystem (Chrome side panel only)? Say the profile can't persist there; recommend Claude Cowork or Claude Code with Claude in Chrome connected.

## Token and accuracy rules

Follow these on every run; they are the difference between a 20K-token run and a 300K-token one.

- **Discover off-browser first.** ATS feeds (`scripts/ats_fetch.py`) and the Indeed connector (if available) return structured jobs with zero page reads.
- **Filter in code, not in context.** Run `scripts/prefilter.py`; only the shortlist reaches you. Never paste whole job lists into the conversation.
- **Read pages as text/structure, never screenshot by default.** Use page-text / accessibility-tree / find-element tools. Screenshot only when an element can't be found structurally, and say why.
- **One JD read per job.** Read once, decide, keep a one-line summary; don't re-read.
- **Answer bank first.** Resolve each screening question with `store.py match --q "..."` before reasoning about it.
- **Verify, don't assume.** After every click that changes state: re-read the page and confirm the expected result (next step, "Applied", "Application sent"). Element refs go stale after navigation; re-find them.
- **Learn once.** When a flow differs from the reference file, append the fix to `recipes.md` (`store.py recipe --platform p --note "..."`).
- **Delegate repetition.** In Claude Code with subagents, hand per-job scoring and form-filling to a smaller/faster model with only the job, profile and answer bank in context; keep orchestration in the main agent.

## Workflow

### 1. Profile
`python3 scripts/store.py status`. If no valid profile → setup: get the resume, extract facts, ask the questions in `references/setup-questions.md` (small groups, skip what the resume answers, confirm inferences), show the draft, save with `store.py init --from draft.json`, seed `answers.json`. If valid → two-line summary + "anything changed?".

### 2. Plan the run
Platforms = user's request, or `automation.platforms` from profile on autopilot. For each: `store.py today --platform p` → remaining budget. Read `recipes.md` once.

### 3. Discover
| Source | How | Reference |
|---|---|---|
| Company career boards | `python3 scripts/ats_fetch.py` (uses targets.json) | `references/ats.md` |
| Indeed | Indeed connector search tools if present; else browser | `references/indeed.md` |
| Naukri | recommended tabs / search in Chrome | `references/naukri.md` |
| LinkedIn | Easy Apply search in Chrome | `references/linkedin.md` |
| Instahyre | Opportunities tab in Chrome | `references/instahyre.md` |
| Wellfound, Cutshort | search in Chrome | `references/startups.md` |
| Hirist | search in Chrome | `references/hirist.md` |

For browser sources, extract only the card fields (id, title, company, location, experience, url, posted) and append them to `jobs.jsonl` with `store.py addjobs --file cards.json` (JSON list). Read the platform reference only when that platform is in the run.

### 4. Prefilter and score
`python3 scripts/prefilter.py --top 40` → writes `shortlist.json` (deduped against applied.jsonl, exclusions removed, heuristic score 0–100). Then for each shortlisted job, up to the platform's remaining budget: read the JD once and make the final call (must-have skills present, experience fits, no exclusion hit, ≥ `min_match_score`). In `approve_batch`, show the final list (title · company · score · one-line reason) and wait for OK.

### 5. Apply
Per the platform reference. For each question: `store.py match` → profile facts → else skip + `store.py pending --add`. Free-text "why you"/notes: write 3–5 sentences tailored to this JD using only resume facts; in `approve_each`/`approve_batch` show it first. Submit per mode, verify confirmation, then `store.py log ...`. Read the next JD before the next submit (natural pacing; never rapid-fire).

### 6. Report
Applied / skipped (grouped reasons) / external links for manual apply / platform warnings / pending questions. Save answers the user gives with `store.py answer`. Increment `supervised_runs.<platform>` with `store.py set` after each supervised run the user watched.

## Autopilot and scheduling

"Run my job hunt" = steps 1–6 over all configured platforms, cheapest first: ATS → Indeed → Naukri → Instahyre → Hirist → Cutshort → Wellfound → LinkedIn.

Schedule via Cowork or Claude in Chrome scheduled tasks (weekdays), only after the supervised threshold. The computer must be awake with Chrome open; a login or OTP wall ends that platform's run, which is the intended behavior. End every scheduled run with the report so the user sees what happened.

## Updating

Profile change → `store.py set --key k --value v` and fix affected `answers.json` entries. New target company → find its board URL (boards.greenhouse.io/<slug>, jobs.lever.co/<slug>, jobs.ashbyhq.com/<slug>) and `store.py target --ats a --slug s --company "Name"`.
