---
name: job-autoapply
description: Applies to jobs on Naukri.com and LinkedIn (Easy Apply) on the user's behalf through Claude in Chrome, using a locally saved candidate profile built from their resume. Use this skill whenever the user wants to auto-apply, bulk-apply, batch-apply or "apply to jobs for me" on Naukri or LinkedIn, set up or update their job-application profile, answer screening questions from their resume, run a daily job-application session, check which jobs were already applied to, or schedule recurring applications — even if they just say "apply to some jobs today" or "run my job hunt".
---

# Job Auto-Apply (Naukri + LinkedIn)

Find matching jobs, fill application forms truthfully from the candidate's real resume, and log every application locally so nothing is applied to twice. The browser work happens in the user's own Chrome via Claude in Chrome, logged in as themselves.

## Ground rules (read first)

These exist to protect the candidate's accounts and reputation, not to slow things down.

1. **Never fabricate.** Every answer (years of experience, skills, CTC, notice period) must trace back to the resume or to something the user told you during setup. An inflated "5 years of Kafka" that gets caught in an interview costs more than one skipped job. If you can't answer a question truthfully from the profile, skip the job and log the question for the user.
2. **Human volume, real browser.** Work only in the user's normal Chrome session. No headless browsers, proxies, second accounts, CAPTCHA solvers or fingerprint tricks. Respect the daily caps in `profile.json` (defaults below). Platform detection targets volume and repetitive patterns; the reliable way to stay safe is low volume and genuinely relevant applications.
3. **Stop on any platform pushback.** CAPTCHA, OTP prompt, "unusual activity", "you've reached today's limit", login wall, or a restriction notice → stop the run immediately, log it, and tell the user. Do not try to get around it.
4. **LinkedIn needs extra care.** LinkedIn's User Agreement prohibits automated tools, and restrictions in 2026 are most often triggered by automation. Default LinkedIn to `approve_each` mode (Claude fills, user clicks Submit) and a low cap. Tell the user this once during setup; let them choose, and record their choice.
5. **Approval mode is the user's call.** `approve_each` (pause before every Submit), `approve_batch` (show the shortlist, user OKs it, then submit), or `auto` (submit within caps). First runs are always `approve_each` regardless of setting, until the user has watched at least one full run.

## Local data

Everything lives in `~/job-autoapply/` (create if missing). Use `scripts/store.py` for all reads/writes so the format stays consistent.

```
~/job-autoapply/
  profile.json        # candidate profile + preferences + caps (schema: assets/profile.template.json)
  answers.json        # bank of screening question → answer, grown over time
  applied.jsonl       # one line per application attempt (dedup + history)
  pending_questions.json  # questions you couldn't answer, for the user to fill
  resumes/            # resume file(s) the user provided
```

If there's no filesystem (e.g. running only in the Chrome side panel), tell the user the profile can't persist there and suggest running from Claude Cowork or Claude Code with Claude in Chrome connected.

## Workflow

### Step 1 — Load or build the profile

Run `python3 scripts/store.py status`. If a valid profile exists, summarize it in two lines and ask if anything changed (new CTC, notice period, location). Then go to Step 2.

If not, run setup:

1. **Ask for the resume** (PDF/DOCX upload or path). Copy it into `resumes/`. Extract: name, email, phone, current title/company, total experience, per-skill experience (estimate per skill only from dated roles that mention it; mark estimates as such), education, past companies, key projects.
2. **Ask the clarification questions** in `references/setup-questions.md`. Ask in small groups (3–4 at a time, using tappable options where the tool exists), skip anything the resume already answers, and confirm what you inferred instead of re-asking.
3. **Show the draft profile** in plain language and get a yes before saving. Pay special attention to per-skill years — have the user confirm or correct each.
4. Save with `python3 scripts/store.py init --from <draft.json>`, which validates against the template.
5. Seed `answers.json` with the common screening answers from setup (notice period, CTC, relocation, years in top skills, work authorization).

### Step 2 — Pick the platform and plan the run

Ask which platform(s) for this run if not stated. Check today's count with `python3 scripts/store.py today --platform naukri|linkedin`. Remaining budget = cap − today's count. If zero, say so and stop.

Then read the platform reference:
- Naukri → `references/naukri.md`
- LinkedIn → `references/linkedin.md`

### Step 3 — Find and score jobs

Collect candidate jobs per the platform reference. For each, before opening the apply flow:

- `python3 scripts/store.py seen --platform <p> --job-id <id>` → skip if already applied/skipped.
- Score 0–100 against the profile: role title fit (30), must-have skill overlap (40), experience range fit (15), location/remote fit (10), exclusions clear (5). Hard-skip anything matching `exclusions` (companies, role keywords) or below `min_match_score`.
- Rank, take the top N where N = remaining budget.

In `approve_batch` mode, show the shortlist (title, company, location, score, one-line reason) and wait for the OK.

### Step 4 — Apply

Follow the platform reference for the form flow. For each screening question:

1. Look it up in `answers.json` (match by meaning, not exact text — "notice period in days" and "How soon can you join?" are the same question).
2. Else derive it from `profile.json` if the answer is directly there.
3. Else: don't guess. Close the form without submitting, log the job as `skipped_question`, and add the question to `pending_questions.json`.

Before Submit in `approve_each`, show: job, company, every question with the answer you entered. After submit, verify the confirmation on screen (don't assume success), then log:

`python3 scripts/store.py log --platform <p> --job-id <id> --title "..." --company "..." --url "..." --score 82 --status applied|skipped|skipped_question|failed|external --note "..."`

Leave a natural gap between applications (read the next job description properly before applying — that alone paces things). Never rapid-fire.

### Step 5 — Wrap up

Report: applied count, skipped (with reasons grouped), any platform warnings, and the pending questions. Ask the user to answer pending questions; save answers with `python3 scripts/store.py answer --q "..." --a "..."` so next run handles them.

## Scheduling

If the user wants recurring runs: suggest weekday scheduling via Cowork scheduled tasks / Claude in Chrome scheduled tasks, after at least two supervised runs. Warn that scheduled tasks need the computer awake and Chrome open, and that a login/OTP wall will stop an unattended run (which is the correct behavior — it should log and notify, not push through). Scheduled runs should use `approve_batch` or `auto` on Naukri only; keep LinkedIn supervised.

## Updating the profile

When the user says something changed ("my notice is now 30 days", "add Go"), update via `python3 scripts/store.py set --key <dotted.key> --value <json>` and also fix any affected entries in `answers.json`.
