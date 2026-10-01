#!/usr/bin/env python3
"""Local storage for job-autoapply: profile, answer bank, application log.

Usage:
  store.py status
  store.py init --from draft.json
  store.py set --key facts.notice_period_days --value 30
  store.py today --platform naukri
  store.py seen --platform naukri --job-id 123
  store.py log --platform naukri --job-id 123 --title T --company C --url U --score 80 --status applied [--note N]
  store.py answer --q "Notice period?" --a "30 days"
  store.py answers
  store.py pending [--add "question" --platform p --job-id id]
  store.py history [--days 7]
"""
import argparse, json, os, sys, datetime as dt
from pathlib import Path

HOME = Path(os.environ.get("JOB_AUTOAPPLY_HOME", Path.home() / "job-autoapply"))
TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "profile.template.json"
HARD_MAX = {"naukri": 40, "linkedin": 25}
STATUSES = {"applied", "skipped", "skipped_question", "failed", "external"}

def p(name): return HOME / name

def load(name, default):
    f = p(name)
    if not f.exists(): return default
    return json.loads(f.read_text())

def save(name, data):
    HOME.mkdir(parents=True, exist_ok=True)
    tmp = p(name + ".tmp"); tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False)); tmp.replace(p(name))

def entries():
    f = p("applied.jsonl")
    if not f.exists(): return []
    return [json.loads(l) for l in f.read_text().splitlines() if l.strip()]

def validate(profile):
    tmpl = json.loads(TEMPLATE.read_text()); errs = []
    def walk(t, d, path):
        for k, v in t.items():
            if k not in d: errs.append(f"missing {path}{k}")
            elif isinstance(v, dict) and isinstance(d[k], dict) and k != "skill_years": walk(v, d[k], f"{path}{k}.")
    walk(tmpl, profile, "")
    c = profile.get("candidate", {})
    for k in ("name", "email"):
        if not c.get(k): errs.append(f"candidate.{k} empty")
    a = profile.get("automation", {})
    for plat, mx in HARD_MAX.items():
        cap = a.get(plat, {}).get("daily_cap", 0)
        if cap > mx: errs.append(f"automation.{plat}.daily_cap {cap} exceeds hard max {mx}")
        if a.get(plat, {}).get("mode") not in ("approve_each", "approve_batch", "auto"):
            errs.append(f"automation.{plat}.mode invalid")
    return errs

def today_count(platform):
    d = dt.date.today().isoformat()
    return sum(1 for e in entries() if e["platform"] == platform and e["status"] == "applied" and e["ts"][:10] == d)

def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    s = sub.add_parser("init"); s.add_argument("--from", dest="src", required=True)
    s = sub.add_parser("set"); s.add_argument("--key", required=True); s.add_argument("--value", required=True)
    s = sub.add_parser("today"); s.add_argument("--platform", required=True)
    s = sub.add_parser("seen"); s.add_argument("--platform", required=True); s.add_argument("--job-id", required=True)
    s = sub.add_parser("log")
    for a in ("platform", "job-id", "title", "company", "url", "status"): s.add_argument("--" + a, required=True)
    s.add_argument("--score", type=int, default=None); s.add_argument("--note", default="")
    s = sub.add_parser("answer"); s.add_argument("--q", required=True); s.add_argument("--a", required=True)
    sub.add_parser("answers")
    s = sub.add_parser("pending"); s.add_argument("--add"); s.add_argument("--platform"); s.add_argument("--job-id")
    s = sub.add_parser("history"); s.add_argument("--days", type=int, default=7)
    a = ap.parse_args()

    if a.cmd == "status":
        prof = load("profile.json", None)
        if prof is None: print(json.dumps({"profile": None, "home": str(HOME)})); return
        errs = validate(prof)
        print(json.dumps({"home": str(HOME), "valid": not errs, "errors": errs,
            "name": prof["candidate"].get("name"), "titles": prof["prefs"].get("target_titles"),
            "today": {k: today_count(k) for k in HARD_MAX},
            "caps": {k: prof["automation"].get(k, {}).get("daily_cap") for k in HARD_MAX},
            "answers": len(load("answers.json", {})), "pending": len(load("pending_questions.json", []))}, indent=2))
    elif a.cmd == "init":
        prof = json.loads(Path(a.src).read_text()); errs = validate(prof)
        if errs: print("INVALID:\n" + "\n".join(errs)); sys.exit(1)
        (HOME / "resumes").mkdir(parents=True, exist_ok=True); save("profile.json", prof)
        if not p("answers.json").exists(): save("answers.json", {})
        print(f"saved {p('profile.json')}")
    elif a.cmd == "set":
        prof = load("profile.json", None)
        if prof is None: print("no profile"); sys.exit(1)
        try: val = json.loads(a.value)
        except json.JSONDecodeError: val = a.value
        cur = prof; keys = a.key.split(".")
        for k in keys[:-1]: cur = cur.setdefault(k, {})
        cur[keys[-1]] = val; errs = validate(prof)
        if errs: print("INVALID:\n" + "\n".join(errs)); sys.exit(1)
        save("profile.json", prof); print(f"{a.key} = {json.dumps(val)}")
    elif a.cmd == "today":
        prof = load("profile.json", {}); cap = prof.get("automation", {}).get(a.platform, {}).get("daily_cap", 0)
        cap = min(cap, HARD_MAX.get(a.platform, 0)); n = today_count(a.platform)
        print(json.dumps({"platform": a.platform, "applied_today": n, "cap": cap, "remaining": max(0, cap - n)}))
    elif a.cmd == "seen":
        hit = [e for e in entries() if e["platform"] == a.platform and str(e["job_id"]) == str(a.job_id)]
        print(json.dumps({"seen": bool(hit), "last": hit[-1] if hit else None}))
    elif a.cmd == "log":
        if a.status not in STATUSES: print(f"status must be one of {sorted(STATUSES)}"); sys.exit(1)
        e = {"ts": dt.datetime.now().isoformat(timespec="seconds"), "platform": a.platform, "job_id": a.job_id,
             "title": a.title, "company": a.company, "url": a.url, "score": a.score, "status": a.status, "note": a.note}
        HOME.mkdir(parents=True, exist_ok=True)
        with open(p("applied.jsonl"), "a") as f: f.write(json.dumps(e, ensure_ascii=False) + "\n")
        print(json.dumps({"logged": True, "applied_today": today_count(a.platform)}))
    elif a.cmd == "answer":
        bank = load("answers.json", {}); bank[a.q] = a.a; save("answers.json", bank)
        pend = [x for x in load("pending_questions.json", []) if x["question"] != a.q]; save("pending_questions.json", pend)
        print(f"saved ({len(bank)} answers)")
    elif a.cmd == "answers":
        print(json.dumps(load("answers.json", {}), indent=2, ensure_ascii=False))
    elif a.cmd == "pending":
        pend = load("pending_questions.json", [])
        if a.add:
            if not any(x["question"] == a.add for x in pend):
                pend.append({"question": a.add, "platform": a.platform, "job_id": a.job_id,
                             "ts": dt.datetime.now().isoformat(timespec="seconds")})
                save("pending_questions.json", pend)
        print(json.dumps(pend, indent=2, ensure_ascii=False))
    elif a.cmd == "history":
        cut = (dt.date.today() - dt.timedelta(days=a.days)).isoformat()
        rows = [e for e in entries() if e["ts"][:10] >= cut]; summary = {}
        for e in rows: summary.setdefault(e["platform"], {}).setdefault(e["status"], 0); summary[e["platform"]][e["status"]] += 1
        print(json.dumps({"days": a.days, "summary": summary, "recent": rows[-20:]}, indent=2, ensure_ascii=False))

if __name__ == "__main__": main()
