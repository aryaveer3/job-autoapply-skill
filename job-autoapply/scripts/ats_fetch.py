#!/usr/bin/env python3
"""Fetch jobs from public Greenhouse / Lever / Ashby job-board APIs into jobs.jsonl.

Usage: ats_fetch.py [--only-title-match] [--max-per-company 20] [--fixture-dir DIR]
No browser, no login. Replaces previous 'ats' rows in jobs.jsonl; keeps rows from other platforms.
"""
import argparse, html, json, os, re, sys, urllib.request, urllib.error, datetime as dt
from pathlib import Path

HOME = Path(os.environ.get("JOB_AUTOAPPLY_HOME", Path.home() / "job-autoapply"))
URLS = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true",
    "lever": "https://api.lever.co/v0/postings/{slug}?mode=json",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true",
}
DESC_MAX = 1500

def clean(s):
    s = html.unescape(s or ""); s = re.sub(r"<(br|/p|/li|/h\d)[^>]*>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s); s = html.unescape(s)
    s = re.sub(r"[ \t]+", " ", s); s = re.sub(r"\n\s*\n+", "\n", s)
    return s.strip()[:DESC_MAX]

def get(ats, slug, fixture_dir):
    if fixture_dir:
        return json.loads((Path(fixture_dir) / f"{ats}_{slug}.json").read_text())
    req = urllib.request.Request(URLS[ats].format(slug=slug), headers={"User-Agent": "job-autoapply/2 (personal job search)"})
    with urllib.request.urlopen(req, timeout=30) as r: return json.loads(r.read().decode())

def ms_to_iso(v):
    try: return dt.datetime.fromtimestamp(int(v) / 1000, dt.timezone.utc).isoformat()
    except Exception: return None

def normalize(ats, slug, company, data):
    rows = []
    if ats == "greenhouse":
        for j in data.get("jobs", []):
            rows.append({"job_id": j.get("id"), "title": j.get("title"), "location": (j.get("location") or {}).get("name", ""),
                         "url": j.get("absolute_url"), "apply_url": j.get("absolute_url"), "posted": j.get("updated_at"),
                         "description": clean(j.get("content"))})
    elif ats == "lever":
        for j in data if isinstance(data, list) else []:
            c = j.get("categories") or {}
            rows.append({"job_id": j.get("id"), "title": j.get("text"), "location": c.get("location", ""),
                         "workplace": j.get("workplaceType"), "url": j.get("hostedUrl"), "apply_url": j.get("applyUrl") or j.get("hostedUrl"),
                         "posted": ms_to_iso(j.get("createdAt")), "description": clean(j.get("descriptionPlain") or j.get("description"))})
    elif ats == "ashby":
        for j in data.get("jobs", []):
            if j.get("isListed") is False: continue
            rows.append({"job_id": j.get("id"), "title": j.get("title"), "location": j.get("location", ""),
                         "workplace": "remote" if j.get("isRemote") else j.get("workplaceType"), "url": j.get("jobUrl"),
                         "apply_url": j.get("applyUrl") or j.get("jobUrl"), "posted": j.get("publishedAt"),
                         "description": clean(j.get("descriptionPlain") or j.get("descriptionHtml"))})
    for r in rows:
        r.update({"platform": "ats", "ats": ats, "board": slug, "company": company, "job_id": f"{ats}:{slug}:{r['job_id']}"})
    return rows

def title_ok(title, targets):
    t = (title or "").lower()
    toks = {w for tt in targets for w in re.findall(r"[a-z0-9+#]+", tt.lower()) if len(w) > 2}
    return not targets or any(w in t for w in toks)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only-title-match", action="store_true"); ap.add_argument("--max-per-company", type=int, default=20)
    ap.add_argument("--fixture-dir")
    a = ap.parse_args()
    targets = json.loads((HOME / "targets.json").read_text()) if (HOME / "targets.json").exists() else []
    if not targets: print(json.dumps({"error": "no targets; add with store.py target"})); sys.exit(1)
    prof = json.loads((HOME / "profile.json").read_text()) if (HOME / "profile.json").exists() else {}
    titles = prof.get("prefs", {}).get("target_titles", [])
    done = set()
    if (HOME / "applied.jsonl").exists():
        done = {(e["platform"], str(e["job_id"])) for e in map(json.loads, filter(str.strip, (HOME / "applied.jsonl").read_text().splitlines()))}
    out, report = [], []
    for t in targets:
        try:
            rows = normalize(t["ats"], t["slug"], t.get("company") or t["slug"], get(t["ats"], t["slug"], a.fixture_dir))
        except (urllib.error.URLError, json.JSONDecodeError, FileNotFoundError, TimeoutError) as e:
            report.append({"board": f"{t['ats']}:{t['slug']}", "error": str(e)[:120]}); continue
        total = len(rows)
        if a.only_title_match: rows = [r for r in rows if title_ok(r["title"], titles)]
        rows = [r for r in rows if ("ats", str(r["job_id"])) not in done][: a.max_per_company]
        out += rows; report.append({"board": f"{t['ats']}:{t['slug']}", "total": total, "kept": len(rows)})
    jf = HOME / "jobs.jsonl"
    keep = [l for l in jf.read_text().splitlines() if l.strip() and json.loads(l).get("platform") != "ats"] if jf.exists() else []
    jf.write_text("\n".join(keep + [json.dumps(r, ensure_ascii=False) for r in out]) + "\n")
    print(json.dumps({"kept": len(out), "boards": report}, indent=2))

if __name__ == "__main__": main()
