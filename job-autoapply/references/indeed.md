# Indeed

## Discover (prefer the connector)
If an Indeed connector is available (tools like search_jobs / get_job_details), use it: query by target title + location, then fetch details only for prefiltered jobs. Convert results to the normalized job shape (platform `indeed`, job_id, title, company, location, url, description) and add them with `store.py addjobs`. Zero page reads.

Without the connector: search on in.indeed.com in Chrome and read cards only.

## Apply
- **Easily apply / Indeed Apply**: multi-step modal (contact → resume → employer questions → review → submit). Same question rules as everywhere else. Confirm "Your application has been submitted".
- **Apply on company site**: if it lands on Greenhouse/Lever/Ashby, follow `references/ats.md`; otherwise log `external`.
- Default cap 15/day (hard max 30). Indeed account login or verification walls → stop.
