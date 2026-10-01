# Setup clarification questions

Ask only what the resume doesn't already answer. Confirm inferred values ("Your resume shows ~3 years in Java — correct?") instead of asking cold. Group 3–4 questions per turn.

## Group A — Targeting
- Target job titles (offer 3–5 inferred from resume; user picks/edits)
- Must-have keywords (skills a job must mention) and nice-to-have keywords
- Seniority / experience range to target (e.g. 2–5 years)
- Locations: cities, remote OK?, hybrid OK?, willing to relocate?

## Group B — Application facts (asked by almost every screener)
- Total experience (years, decimal OK) — confirm resume-derived value
- Per-skill years for the top 6–10 skills — confirm each
- Current CTC and expected CTC (LPA); open to negotiation?
- Notice period (days); serving notice? last working day? buyout possible?
- Current location
- Work authorization (for India roles usually "Indian citizen, no sponsorship needed"; for overseas roles ask)
- Highest education + graduation year (confirm)

## Group C — Filters
- Companies to exclude (current employer, ex-employers, anything else)
- Role keywords to exclude (e.g. "Frontend", "QA", "Sales", "Intern")
- Minimum company/job quality bar? (e.g. skip consultancies / staffing agencies: yes/no)
- Minimum match score (default 65)

## Group D — Automation settings
- Platforms: any of ats (company career sites), indeed, naukri, instahyre, hirist, cutshort, wellfound, linkedin
- Target companies for career-board watching (names or careers URLs; resolve to Greenhouse/Lever/Ashby slugs and save with `store.py target`)
- Approval mode per platform: approve_each / approve_batch / auto (explain LinkedIn ToS risk; recommend approve_each on LinkedIn)
- Daily cap per platform (defaults / script hard max): ats 15/40, indeed 15/30, naukri 15/40, instahyre 20/30, hirist 15/30, cutshort 10/20, wellfound 8/15, linkedin 10/25
- Which resume file to upload when a form asks (if multiple)
- Optional: a 2–3 line cover note to reuse when a form has a free-text "why you" box (draft one from the resume; user approves)

## Questions you should NOT pre-answer
Diversity/EEO, disability, gender, caste, religion, date of birth, marital status: answer only with "Prefer not to say"/decline option if one exists; otherwise ask the user per case. Do not store these in the profile unless the user explicitly asks.
