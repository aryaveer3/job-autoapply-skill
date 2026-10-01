# job-autoapply — Claude skill for Naukri & LinkedIn

A [Claude skill](https://docs.claude.com) that helps you apply to jobs on **Naukri.com** and **LinkedIn Easy Apply** through **Claude in Chrome**, using a candidate profile built from your resume and stored locally.

## Features
- **Resume-first setup**: reads your resume, then asks only the clarifying questions it can't answer (CTC, notice period, per-skill years, exclusions, caps).
- **Local storage** in `~/job-autoapply/`: profile, a growing screening-answer bank, an application log for de-duplication, and pending questions.
- **Job scoring** against your profile, with a minimum-match threshold and exclusion filters.
- **Truthful answers only**: if a screening question can't be answered from your profile, the job is skipped and the question is saved for you.
- **Approval modes**: `approve_each`, `approve_batch`, `auto`.
- **Conservative caps**: Naukri defaults to 15/day (hard max 40); LinkedIn defaults to 10/day (hard max 25).

## Install
- **Claude.ai / Desktop / Cowork**: upload `job-autoapply.skill` under Settings → Capabilities → Skills.
- **Claude Code**: copy `job-autoapply/` into `~/.claude/skills/`.

It needs Claude in Chrome and a filesystem (Cowork or Claude Code) to save the profile locally.

## Usage
```
Set up my job profile from this resume
Apply to backend jobs on Naukri today
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
  references/naukri.md         # Naukri apply flow
  references/linkedin.md       # LinkedIn Easy Apply flow
  references/setup-questions.md
  assets/profile.template.json
  scripts/store.py             # local profile / answers / log CLI
job-autoapply.skill            # packaged, ready to install
```

## License
MIT
