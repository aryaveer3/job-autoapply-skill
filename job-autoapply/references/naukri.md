# Naukri.com apply flow

Page layouts change; treat selectors below as hints and read the actual page. If something looks very different, describe what you see to the user before acting.

## Limits
- Naukri's own stated limit is 50 applications per day. Stay well under it: default cap 15, script hard max 40.
- Naukri itself caps applications per day; hitting a limit message means stop.

## Pre-flight
1. Open `https://www.naukri.com/mnjuser/homepage`. If you land on a login page, stop and ask the user to log in themselves (never type passwords; OTP is theirs to handle).
2. Optional, only if user asked: check profile completeness banner and mention it — a complete, recently updated profile gets more recruiter views than extra applications do.

## Finding jobs (pick per user preference)
- **Recommended jobs** (`/mnjuser/recommendedjobs`): tabs such as Profile, Applies, Preferences, You might like. Good default — these are already matched.
- **Search**: `https://www.naukri.com/<keyword>-jobs-in-<city>?experience=<years>` plus filters (freshness "Last 3/7 days", work mode, salary). Prefer recent postings.
- For each card collect: job ID (from URL, the trailing number in `/job-listings-...-<id>`), title, company, experience range, salary if shown, location, posted date.

## Skip before opening
- "Apply on company site" → these leave Naukri. Log as `external` with the URL so the user can apply manually; do not fill third-party ATS forms unless the user asked.
- Already shows "Applied".
- Staffing/consultancy postings if user filtered them.
- Experience range clearly outside profile (e.g. 8–12 yrs for a 3-yr profile).

## Applying
1. Open the job detail page; read the JD and re-score with the full text (card text is incomplete).
2. Click **Apply**.
3. Outcomes:
   - Instant "Applied" confirmation → verify, log `applied`.
   - **Questionnaire / chatbot drawer** (recruiter screening, often 1–5 questions: radio, text, numeric, multi-select). Answer each from answers.json/profile per SKILL.md Step 4. Numeric fields: numbers only (e.g. `3` not "3 years"). CTC fields: check whether it wants LPA or absolute rupees from the placeholder. Then the drawer's Save/Submit button.
   - If any question can't be answered truthfully → close the drawer without submitting, log `skipped_question`, add to pending_questions.
4. Confirm the "applied" state on screen before logging.

## Common Naukri screening questions → profile keys
| Question pattern | Source |
|---|---|
| Notice period / how soon can you join | `facts.notice_period_days` |
| Current CTC / expected CTC | `facts.current_ctc_lpa`, `facts.expected_ctc_lpa` |
| Years of experience in X | `facts.skill_years.X` (skip if X absent) |
| Total experience | `facts.total_experience_years` |
| Current location / willing to relocate to Y | `facts.current_location`, `prefs.willing_to_relocate` |
| Comfortable with WFO / hybrid / shifts | `prefs.work_modes`; shifts → ask user once, then store |
| Rate yourself in X (1–10) | ask user once per skill, store in answers.json |
