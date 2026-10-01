# job-autoapply — AI job-application copilot (Claude skill)

A [Claude skill](https://docs.claude.com) that finds matching jobs and applies for you across **company career sites (Greenhouse, Lever, Ashby)**, **Indeed**, **Naukri**, **Instahyre**, **Hirist**, **Cutshort**, **Wellfound** and **LinkedIn Easy Apply**, using a candidate profile built from your resume and stored locally.

## Features
- **API-first discovery**: company boards via public Greenhouse/Lever/Ashby JSON feeds and Indeed via connector — no browser, near-zero tokens.
- **Code-side prefilter** (`prefilter.py`): dedupes (including the same role across platforms), applies exclusions, scores 0–100 — only a shortlist reaches the model.
- **Deterministic answer bank** (`store.py match`): resolves screening questions without LLM reasoning; skill-years only from verified profile data.
- **Autopilot**: "run my job hunt" runs all platforms cheapest-first, with per-platform caps and modes, and a final report.
- **Learned recipes**: site quirks are saved to `recipes.md` so later runs don't rediscover them.
- **Resume-first setup**: reads your resume, then asks only the clarifying questions it can't answer (CTC, notice period, per-skill years, exclusions, caps).
- **Local storage** in `~/job-autoapply/`: profile, a growing screening-answer bank, an application log for de-duplication, and pending questions.
- **Job scoring** against your profile, with a minimum-match threshold and exclusion filters.
- **Truthful answers only**: if a screening question can't be answered from your profile, the job is skipped and the question is saved for you.
- **Approval modes**: `approve_each`, `approve_batch`, `auto`.
- **Conservative caps** (default / hard max per day): ats 15/40, indeed 15/30, naukri 15/40, instahyre 20/30, hirist 15/30, cutshort 10/20, wellfound 8/15, linkedin 10/25.
- **Supervised start**: each platform runs approve-each for its first 2 runs before your chosen mode kicks in.

## Install
- **Claude.ai / Desktop / Cowork**: upload `job-autoapply.skill` under Settings → Capabilities → Skills.
- **Claude Code**: copy `job-autoapply/` into `~/.claude/skills/`.

It needs Claude in Chrome and a filesystem (Cowork or Claude Code) to save the profile locally.

## Usage
```
Set up my job profile from this resume
Apply to backend jobs on Naukri today
Add Stripe, Razorpay and Swiggy to my target companies
Run my job hunt
Show my application history for the last 7 days
```

## Important
- LinkedIn's User Agreement prohibits automated tools. Using automation there risks account restriction, so this skill defaults LinkedIn to manual submit. Use at your own risk.
- The skill does **not** attempt to evade bot detection. It stops on any CAPTCHA, OTP, limit message, or restriction notice.
- Never commit your `~/job-autoapply/` folder. It contains personal data.

## Layout
```
job-autoapply/
  SKILL.md                     # workflow
  references/ats.md            # Greenhouse / Lever / Ashby
  references/naukri.md  linkedin.md  instahyre.md  hirist.md  indeed.md  startups.md
  references/setup-questions.md
  assets/profile.template.json
  scripts/store.py             # profile, answer matching, log, targets, recipes
  scripts/ats_fetch.py         # public ATS job feeds -> jobs.jsonl
  scripts/prefilter.py         # dedupe + score -> shortlist.json
job-autoapply.skill            # packaged, ready to install
```

## License
MIT
