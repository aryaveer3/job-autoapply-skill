# LinkedIn Easy Apply flow

## Risk, stated plainly
LinkedIn's User Agreement prohibits bots and automated methods. Their detection looks at volume, speed, repetitive patterns and automation frameworks, and account restrictions range from a short cooldown to permanent loss of the account. There is no "safe undetectable" method, and this skill does not try to be one. What lowers risk: the user's own normal browser, low daily volume, genuinely relevant applications, and the user clicking Submit. Say this once at setup; respect the user's choice; record it in `profile.json` as `automation.linkedin.tos_risk_acknowledged`. Modes other than `approve_each` require that flag to be true (the script enforces it).

## Limits
- Default cap 10/day, script hard max 25. LinkedIn also shows its own daily Easy Apply limit message — stop when it appears.
- Keep the account doing normal things too; a profile that only ever fires Easy Apply looks unusual. Don't automate connections, messages or profile views — out of scope for this skill.

## Pre-flight
1. Open `https://www.linkedin.com/jobs/`. Login wall or verification checkpoint → stop; the user signs in themselves.
2. Any "restricted" / "unusual activity" banner → stop the whole run and tell the user.

## Finding jobs
- Search: `https://www.linkedin.com/jobs/search/?keywords=<title>&location=<city>&f_AL=true&f_TPR=r604800` (`f_AL=true` = Easy Apply only, `f_TPR=r604800` = past week; `r86400` = past 24h). Add `f_WT=2` for remote.
- Job ID: the number in `currentJobId=` or `/jobs/view/<id>/`.
- Skip: "Applied" badge, Promoted roles from excluded companies, non-Easy-Apply ("Apply" with external arrow → log `external` with URL).

## Easy Apply modal (multi-step)
1. Click **Easy Apply**. Steps vary per job; typical sequence:
   - **Contact info**: prefilled from profile — verify email/phone match `profile.json`, don't edit unless wrong.
   - **Resume**: select the user's chosen resume (or upload from `resumes/`).
   - **Additional questions**: numeric years-of-experience boxes, yes/no radios, dropdowns, short text. Answer per SKILL.md Step 4. Numeric boxes reject decimals on some jobs — round down (never up).
   - **Work authorization / sponsorship**: from `facts.work_authorization`.
   - **Voluntary self-identification**: choose "Prefer not to say"/"I don't wish to answer".
   - **Review**: read every field back.
2. Uncheck "Follow <company>" unless the user wants it.
3. Submit only per approval mode (default: show the review summary and let the user click Submit).
4. If a required question can't be answered truthfully → Dismiss → "Discard" (not "Save", to avoid half-finished drafts), log `skipped_question`.
5. Confirm "Application sent" before logging `applied`.

## Common question patterns
| Pattern | Source |
|---|---|
| How many years of work experience do you have with X? | `facts.skill_years.X` (round down) |
| Are you legally authorized to work in <country>? | `facts.work_authorization` |
| Will you require sponsorship? | `facts.needs_sponsorship` |
| Are you comfortable commuting/relocating to Y? | `prefs.willing_to_relocate`, `prefs.locations` |
| Expected salary / current salary | `facts.expected_ctc_lpa` (check currency/unit asked) |
| Notice period | `facts.notice_period_days` |
| Headline / summary / cover letter box | `cover_note` (user-approved text only) |
