#!/usr/bin/env python3
"""Score jobs.jsonl against profile.json in code so only a short list reaches the model.

Usage: prefilter.py [--top 40] [--platform P] [--min SCORE]
Writes shortlist.json. Heuristic score 0-100: title 30, must-have skills 40, experience 15, location 10, clean 5.
Final decision still needs one JD read per shortlisted job.
"""
import argparse, json, os, re, difflib
from pathlib import Path

HOME = Path(os.environ.get("JOB_AUTOAPPLY_HOME", Path.home() / "job-autoapply"))
STAFFING = re.compile(r"\b(consult\w*|staffing|placement|manpower|recruit\w*|hr services|talent solutions)\b", re.I)

def jl(n):
    f = HOME / n
    return [json.loads(l) for l in f.read_text().splitlines() if l.strip()] if f.exists() else []

def kw_hit(k, text):
    return re.search(r"(?<![a-z0-9])" + re.escape(k.lower()) + r"(?![a-z0-9])", text) is not None

def exp_range(s):
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:-|to|–)\s*(\d+(?:\.\d+)?)\s*(?:\+?\s*)?(?:yrs?|years?)", s or "", re.I)
    if m: return float(m.group(1)), float(m.group(2))
    m = re.search(r"(\d+(?:\.\d+)?)\s*\+\s*(?:yrs?|years?)", s or "", re.I)
    if m: return float(m.group(1)), 99.0
    m = re.search(r"(?:minimum|at least|min\.?)\s*(\d+(?:\.\d+)?)\s*(?:yrs?|years?)", s or "", re.I)
    if m: return float(m.group(1)), 99.0
    return None

def score(job, prof):
    pr, f, ex = prof.get("prefs", {}), prof.get("facts", {}), prof.get("exclusions", {})
    title = (job.get("title") or "").lower(); company = (job.get("company") or "").lower()
    text = " ".join(str(job.get(k) or "") for k in ("title", "description", "skills", "experience")).lower()
    for c in ex.get("companies", []):
        if c.lower() and c.lower() in company: return None, f"excluded company {c}"
    for k in ex.get("role_keywords", []):
        if k.lower() and kw_hit(k, title): return None, f"excluded role keyword {k}"
    if ex.get("skip_staffing_agencies") and STAFFING.search(company): return None, "staffing agency"
    b = {}
    tt = pr.get("target_titles", [])
    b["title"] = round(30 * max([difflib.SequenceMatcher(None, title, t.lower()).ratio() for t in tt] or [0.5]), 1)
    must = pr.get("must_have_keywords", [])
    has_desc = len(job.get("description") or "") > 200
    if must:
        frac = sum(kw_hit(k, text) for k in must) / len(must)
        b["skills"] = round(40 * (frac if has_desc else max(frac, 0.5)), 1)
    else: b["skills"] = 20
    nice = pr.get("nice_to_have_keywords", [])
    if nice: b["skills"] = min(40, b["skills"] + 5 * sum(kw_hit(k, text) for k in nice) / len(nice))
    yrs = f.get("total_experience_years") or 0
    rng = exp_range(str(job.get("experience") or "")) or exp_range(job.get("description") or "")
    if rng is None: b["experience"] = 8
    elif rng[0] <= yrs <= rng[1]: b["experience"] = 15
    elif rng[0] - 1 <= yrs <= rng[1] + 2: b["experience"] = 7
    elif yrs < rng[0] - 1: return None, f"needs {rng[0]:g}+ yrs"
    else: b["experience"] = 0
    loc = f"{job.get('location') or ''} {job.get('workplace') or ''}".lower()
    locs = [l.lower() for l in pr.get("locations", [])]
    remote_ok = "remote" in [m.lower() for m in pr.get("work_modes", [])]
    if not loc.strip(): b["location"] = 5
    elif any(l in loc for l in locs) or (remote_ok and "remote" in loc): b["location"] = 10
    elif pr.get("willing_to_relocate"): b["location"] = 6
    else: b["location"] = 0
    b["clean"] = 5
    return round(sum(b.values())), b

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--platform"); ap.add_argument("--min", type=int)
    a = ap.parse_args()
    prof = json.loads((HOME / "profile.json").read_text())
    floor = a.min if a.min is not None else max(0, prof.get("automation", {}).get("min_match_score", 65) - 15)
    done = {(e["platform"], str(e["job_id"])) for e in jl("applied.jsonl")}
    done_ct = {((e.get("company") or "").lower(), (e.get("title") or "").lower()) for e in jl("applied.jsonl") if e["status"] == "applied"}
    seen, kept, dropped = set(), [], {}
    for j in jl("jobs.jsonl"):
        if a.platform and j.get("platform") != a.platform: continue
        key = (j.get("platform"), str(j.get("job_id")))
        ct = ((j.get("company") or "").lower(), (j.get("title") or "").lower())
        if key in done or key in seen: dropped["already_seen"] = dropped.get("already_seen", 0) + 1; continue
        if ct in done_ct: dropped["same_role_applied_elsewhere"] = dropped.get("same_role_applied_elsewhere", 0) + 1; continue
        seen.add(key)
        s, b = score(j, prof)
        if s is None:
            lbl = "experience" if b.startswith("needs") else " ".join(b.split(" ")[:2])
            dropped[lbl] = dropped.get(lbl, 0) + 1; continue
        if s < floor: dropped["low_score"] = dropped.get("low_score", 0) + 1; continue
        kept.append({k: j.get(k) for k in ("platform", "job_id", "title", "company", "location", "url", "apply_url", "posted") if j.get(k)} | {"score": s, "breakdown": b})
    # cross-platform duplicate: same company+title → keep the cheapest/safest platform
    order = ["ats", "indeed", "naukri", "instahyre", "hirist", "cutshort", "wellfound", "linkedin"]
    kept.sort(key=lambda r: (-r["score"], order.index(r["platform"]) if r["platform"] in order else 99))
    uniq, ctset = [], set()
    for r in kept:
        ct = (r.get("company", "").lower(), r.get("title", "").lower())
        if ct in ctset: dropped["cross_platform_dup"] = dropped.get("cross_platform_dup", 0) + 1; continue
        ctset.add(ct); uniq.append(r)
    short = uniq[: a.top]
    (HOME / "shortlist.json").write_text(json.dumps(short, indent=2, ensure_ascii=False))
    per = {}
    for r in short: per[r["platform"]] = per.get(r["platform"], 0) + 1
    print(json.dumps({"shortlisted": len(short), "per_platform": per, "dropped": dropped, "floor": floor,
                      "top5": [f"{r['score']} · {r['title']} · {r.get('company','')} · {r['platform']}" for r in short[:5]]}, indent=2))

if __name__ == "__main__": main()
