# Company career boards (Greenhouse, Lever, Ashby)

The safest, cheapest and most accurate source: public JSON feeds published by the ATS vendors for companies' careers pages. No login, no account, no platform to restrict.

## Discovery (no browser)
`python3 scripts/ats_fetch.py` reads `targets.json`, calls:
- Greenhouse `https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true`
- Lever `https://api.lever.co/v0/postings/{slug}?mode=json`
- Ashby `https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true`

and writes normalized jobs (description trimmed to ~1,500 chars) to `jobs.jsonl`. Options: `--only-title-match` (drop titles not matching target_titles), `--max-per-company 20`.

Finding slugs: the path segment of the careers URL — boards.greenhouse.io/**stripe**, job-boards.greenhouse.io/**stripe**, jobs.lever.co/**plaid**, jobs.ashbyhq.com/**ramp**. Search "<company> careers greenhouse|lever|ashby" if unknown. Companies on Workday/SuccessFactors/custom portals aren't supported for discovery; add them manually via `store.py addjobs`.

## Applying
Hosted apply pages are single-page forms, usually: first/last name, email, phone, resume upload, LinkedIn URL, sometimes current company, location, work authorization, notice period, salary, a few custom questions, and optional EEO/self-ID.

Use Claude in Chrome (or, in Claude Code, Playwright CLI is acceptable here because these are public forms with no account). Flow:
1. Open `apply_url`. Read the form structure once (field labels + required markers).
2. Fill from profile; upload `candidate.resume_file`. Resolve custom questions via `store.py match`.
3. EEO / voluntary self-ID → "Decline to self-identify" or leave optional fields blank.
4. "How did you hear about us" → "Company website" / "Job board".
5. Submit per mode; confirm the thank-you page or message; log with platform `ats`.

Watch for: reCAPTCHA on submit (stop, log `failed`, give the user the link); cover-letter required (write from resume facts, show first unless `auto`); location/visa questions for roles outside India (answer truthfully from `facts.work_authorization`; skip if the role requires authorization the user lacks).

## Workday and other account-based portals
Each company needs its own account and multi-page wizard. Don't create accounts automatically. Log as `external` with the link; if the user is present and asks, assist page by page in `approve_each`.
