# Instahyre

Curated tech matches; good response rates for 2+ year engineers. Low form complexity, so cheap to automate. Default cap 20/day (hard max 30).

## Pre-flight
Open `https://www.instahyre.com/candidate/opportunities/`. Login page → stop; user logs in. Profile status "Actively looking" gives more matches; mention once if not set.

## Discover
The **Opportunities** tab lists jobs matched to the profile. For each card read: company, title, location, experience, and the job id from the "View" link URL. Append to jobs.jsonl via `store.py addjobs`.

## Apply
1. Click **View** on a shortlisted job; read the details once.
2. Click **Apply** (some flows show "Interested"). If a short question set appears, answer via the answer bank.
3. Confirm the applied state, then log.

## Train the matcher
For clearly irrelevant cards (excluded role keywords/companies, wrong stack), click **Not interested**. This improves future matches and keeps the list short — fewer cards to read next run means fewer tokens. Log as `skipped` with note `not_interested`.
