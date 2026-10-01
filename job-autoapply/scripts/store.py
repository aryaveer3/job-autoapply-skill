#!/usr/bin/env python3
"""Local storage for job-autoapply v2: profile, answers, log, targets, jobs, recipes.

Commands:
  status | init --from F | set --key a.b --value V
  today --platform P            remaining budget + effective mode
  seen --platform P --job-id ID
  log --platform P --job-id ID --title T --company C --url U --status S [--score N] [--note N]
  match --q "question"          answer-bank / profile lookup (no LLM needed on a hit)
  answer --q Q --a A | answers | pending [--add Q --platform P --job-id ID]
  addjobs --file cards.json     append normalized jobs to jobs.jsonl
  target --ats greenhouse|lever|ashby --slug S --company C | targets
  recipe --platform P --note N  append a learned site quirk to recipes.md
  history [--days N]
"""
import argparse, json, os, re, sys, difflib, datetime as dt
from pathlib import Path

HOME = Path(os.environ.get("JOB_AUTOAPPLY_HOME", Path.home() / "job-autoapply"))
TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "profile.template.json"
HARD_MAX = {"ats": 40, "indeed": 30, "naukri": 40, "instahyre": 30, "hirist": 30,
            "cutshort": 20, "wellfound": 15, "linkedin": 25}
MODES = ("approve_each", "approve_batch", "auto")
STATUSES = {"applied", "skipped", "skipped_question", "failed", "external"}
ATS = {"greenhouse", "lever", "ashby"}

def p(n): return HOME / n
def load(n, d):
    f = p(n); return json.loads(f.read_text()) if f.exists() else d
def save(n, data):
    HOME.mkdir(parents=True, exist_ok=True)
    t = p(n + ".tmp"); t.write_text(json.dumps(data, indent=2, ensure_ascii=False)); t.replace(p(n))
def jsonl(n):
    f = p(n)
    return [json.loads(l) for l in f.read_text().splitlines() if l.strip()] if f.exists() else []
def out(o): print(json.dumps(o, indent=2, ensure_ascii=False))

def validate(prof):
    tmpl = json.loads(TEMPLATE.read_text()); errs = []
    def walk(t, d, path):
        for k, v in t.items():
            if k not in d: errs.append(f"missing {path}{k}")
            elif isinstance(v, dict) and isinstance(d[k], dict) and k not in ("skill_years", "supervised_runs"):
                walk(v, d[k], f"{path}{k}.")
    walk(tmpl, prof, "")
    c = prof.get("candidate", {})
    for k in ("name", "email"):
        if not c.get(k): errs.append(f"candidate.{k} empty")
    a = prof.get("automation", {})
    for plat, mx in HARD_MAX.items():
        cfg = a.get(plat, {})
        if cfg.get("daily_cap", 0) > mx: errs.append(f"automation.{plat}.daily_cap exceeds hard max {mx}")
        if cfg.get("mode") not in MODES: errs.append(f"automation.{plat}.mode invalid")
    li = a.get("linkedin", {})
    if li.get("mode") != "approve_each" and not li.get("tos_risk_acknowledged"):
        errs.append("automation.linkedin.mode requires tos_risk_acknowledged=true")
    for plat in a.get("platforms", []):
        if plat not in HARD_MAX: errs.append(f"unknown platform {plat}")
    return errs

def today_count(plat):
    d = dt.date.today().isoformat()
    return sum(1 for e in jsonl("applied.jsonl") if e["platform"] == plat and e["status"] == "applied" and e["ts"][:10] == d)

def applied_keys():
    return {(e["platform"], str(e["job_id"])) for e in jsonl("applied.jsonl")}

STOP = set("a an the of in on with for to do you your are is have has how many much what which please".split())
def norm(q):
    toks = [t for t in re.sub(r"[^a-z0-9+#. ]", " ", q.lower()).split() if t not in STOP]
    return " ".join(toks)

def match(q, prof, bank):
    nq = norm(q)
    best, score = None, 0.0
    for k, v in bank.items():
        nk = norm(k); a, b = set(nq.split()), set(nk.split())
        jac = len(a & b) / max(1, len(a | b))
        s = max(difflib.SequenceMatcher(None, nq, nk).ratio(), jac)
        if s > score: best, score = (k, v), s
    if best and score >= 0.8:
        return {"hit": True, "source": "answers", "matched": best[0], "answer": best[1], "confidence": round(score, 2)}
    f, pr = prof.get("facts", {}), prof.get("prefs", {})
    ql = q.lower()
    if re.search(r"\b(years?|yrs?)\b", ql) and not re.search(r"\b(total|overall)\b", ql):
        parts = re.split(r"\b(?:with|in|using|on|of)\s+", ql)
        skill = parts[-1].strip(" ?.")[:40] if len(parts) > 1 else ""
        skill = re.sub(r"\b(experience|work|professional|hands-on)\b", "", skill).strip()
        if skill:
            for k, v in f.get("skill_years", {}).items():
                kl = k.lower()
                if kl == skill or kl.replace(" ", "") == skill.replace(" ", "") or re.search(r"(?<![a-z0-9])" + re.escape(kl) + r"(?![a-z0-9])", skill):
                    return {"hit": True, "source": "profile", "key": f"facts.skill_years.{k}",
                            "answer": int(v) if float(v).is_integer() else v, "note": "numeric boxes: round DOWN"}
            return {"hit": False, "reason": f"no verified years for '{skill}' - skip job, add to pending"}
    rules = [
        (r"notice|join|joining|how soon|availability", "facts.notice_period_days"),
        (r"expected (ctc|salary|compensation)|salary expectation", "facts.expected_ctc_lpa"),
        (r"current (ctc|salary|compensation)", "facts.current_ctc_lpa"),
        (r"total|overall", "facts.total_experience_years"),
        (r"sponsor", "facts.needs_sponsorship"),
        (r"authori[sz]ed|work permit|right to work", "facts.work_authorization"),
        (r"relocat", "prefs.willing_to_relocate"),
        (r"current location|where are you (based|located)", "facts.current_location"),
    ]
    for rx, key in rules:
        if re.search(rx, ql):
            sec, k = key.split(".")
            val = (f if sec == "facts" else pr).get(k)
            if val not in (None, ""):
                return {"hit": True, "source": "profile", "key": key, "answer": val}
    return {"hit": False, "reason": "not in answer bank or profile", "closest": best[0] if best else None,
            "closest_confidence": round(score, 2)}

def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status"); sub.add_parser("answers"); sub.add_parser("targets")
    s = sub.add_parser("init"); s.add_argument("--from", dest="src", required=True)
    s = sub.add_parser("set"); s.add_argument("--key", required=True); s.add_argument("--value", required=True)
    s = sub.add_parser("today"); s.add_argument("--platform", required=True)
    s = sub.add_parser("seen"); s.add_argument("--platform", required=True); s.add_argument("--job-id", required=True)
    s = sub.add_parser("log")
    for x in ("platform", "job-id", "title", "company", "url", "status"): s.add_argument("--" + x, required=True)
    s.add_argument("--score", type=int); s.add_argument("--note", default="")
    s = sub.add_parser("match"); s.add_argument("--q", required=True)
    s = sub.add_parser("answer"); s.add_argument("--q", required=True); s.add_argument("--a", required=True)
    s = sub.add_parser("pending"); s.add_argument("--add"); s.add_argument("--platform"); s.add_argument("--job-id")
    s = sub.add_parser("addjobs"); s.add_argument("--file", required=True)
    s = sub.add_parser("target"); s.add_argument("--ats", required=True); s.add_argument("--slug", required=True); s.add_argument("--company", default="")
    s = sub.add_parser("recipe"); s.add_argument("--platform", required=True); s.add_argument("--note", required=True)
    s = sub.add_parser("history"); s.add_argument("--days", type=int, default=7)
    a = ap.parse_args()
    prof = load("profile.json", None)

    if a.cmd == "status":
        if prof is None: return out({"profile": None, "home": str(HOME)})
        errs = validate(prof); au = prof["automation"]
        out({"home": str(HOME), "valid": not errs, "errors": errs, "name": prof["candidate"].get("name"),
             "titles": prof["prefs"].get("target_titles"), "platforms": au.get("platforms"),
             "today": {k: f"{today_count(k)}/{au.get(k, {}).get('daily_cap')}" for k in au.get("platforms", [])},
             "answers": len(load("answers.json", {})), "pending": len(load("pending_questions.json", [])),
             "targets": len(load("targets.json", []))})
    elif a.cmd == "init":
        prof = json.loads(Path(a.src).read_text()); errs = validate(prof)
        if errs: print("INVALID:\n" + "\n".join(errs)); sys.exit(1)
        (HOME / "resumes").mkdir(parents=True, exist_ok=True); save("profile.json", prof)
        for n, d in (("answers.json", {}), ("targets.json", []), ("pending_questions.json", [])):
            if not p(n).exists(): save(n, d)
        if not p("recipes.md").exists(): p("recipes.md").write_text("# Learned site recipes\n")
        print(f"saved {p('profile.json')}")
    elif a.cmd == "set":
        if prof is None: print("no profile"); sys.exit(1)
        try: val = json.loads(a.value)
        except json.JSONDecodeError: val = a.value
        cur = prof; ks = a.key.split(".")
        for k in ks[:-1]: cur = cur.setdefault(k, {})
        cur[ks[-1]] = val; errs = validate(prof)
        if errs: print("INVALID:\n" + "\n".join(errs)); sys.exit(1)
        save("profile.json", prof); print(f"{a.key} = {json.dumps(val)}")
    elif a.cmd == "today":
        if a.platform not in HARD_MAX: print(f"unknown platform; use one of {sorted(HARD_MAX)}"); sys.exit(1)
        au = (prof or {}).get("automation", {}); cfg = au.get(a.platform, {})
        cap = min(cfg.get("daily_cap", 0), HARD_MAX[a.platform]); n = today_count(a.platform)
        sup = au.get("supervised_runs", {}).get(a.platform, 0)
        mode = cfg.get("mode", "approve_each") if sup >= 2 else "approve_each"
        out({"platform": a.platform, "applied_today": n, "cap": cap, "remaining": max(0, cap - n),
             "effective_mode": mode, "supervised_runs": sup})
    elif a.cmd == "seen":
        hit = [e for e in jsonl("applied.jsonl") if e["platform"] == a.platform and str(e["job_id"]) == str(a.job_id)]
        out({"seen": bool(hit), "last": hit[-1] if hit else None})
    elif a.cmd == "log":
        if a.status not in STATUSES: print(f"status must be one of {sorted(STATUSES)}"); sys.exit(1)
        e = {"ts": dt.datetime.now().isoformat(timespec="seconds"), "platform": a.platform, "job_id": a.job_id,
             "title": a.title, "company": a.company, "url": a.url, "score": a.score, "status": a.status, "note": a.note}
        HOME.mkdir(parents=True, exist_ok=True)
        with open(p("applied.jsonl"), "a") as f: f.write(json.dumps(e, ensure_ascii=False) + "\n")
        out({"logged": True, "applied_today": today_count(a.platform)})
    elif a.cmd == "match":
        out(match(a.q, prof or {}, load("answers.json", {})))
    elif a.cmd == "answer":
        bank = load("answers.json", {}); bank[a.q] = a.a; save("answers.json", bank)
        save("pending_questions.json", [x for x in load("pending_questions.json", []) if x["question"] != a.q])
        print(f"saved ({len(bank)} answers)")
    elif a.cmd == "answers":
        out(load("answers.json", {}))
    elif a.cmd == "pending":
        pend = load("pending_questions.json", [])
        if a.add and not any(norm(x["question"]) == norm(a.add) for x in pend):
            pend.append({"question": a.add, "platform": a.platform, "job_id": a.job_id,
                         "ts": dt.datetime.now().isoformat(timespec="seconds")})
            save("pending_questions.json", pend)
        out(pend)
    elif a.cmd == "addjobs":
        cards = json.loads(Path(a.file).read_text()); done = applied_keys(); n = 0
        with open(p("jobs.jsonl"), "a") as f:
            for c in cards:
                if not c.get("platform") or not c.get("job_id"): continue
                if (c["platform"], str(c["job_id"])) in done: continue
                f.write(json.dumps(c, ensure_ascii=False) + "\n"); n += 1
        out({"added": n, "skipped_already_seen": len(cards) - n})
    elif a.cmd == "target":
        if a.ats not in ATS: print(f"ats must be one of {sorted(ATS)}"); sys.exit(1)
        t = load("targets.json", [])
        if not any(x["ats"] == a.ats and x["slug"] == a.slug for x in t):
            t.append({"ats": a.ats, "slug": a.slug, "company": a.company or a.slug}); save("targets.json", t)
        print(f"{len(t)} targets")
    elif a.cmd == "targets":
        out(load("targets.json", []))
    elif a.cmd == "recipe":
        HOME.mkdir(parents=True, exist_ok=True)
        with open(p("recipes.md"), "a") as f: f.write(f"- [{dt.date.today()}] **{a.platform}**: {a.note}\n")
        print("recipe saved")
    elif a.cmd == "history":
        cut = (dt.date.today() - dt.timedelta(days=a.days)).isoformat()
        rows = [e for e in jsonl("applied.jsonl") if e["ts"][:10] >= cut]; summ = {}
        for e in rows: summ.setdefault(e["platform"], {}).setdefault(e["status"], 0); summ[e["platform"]][e["status"]] += 1
        out({"days": a.days, "summary": summ, "recent": rows[-20:]})

if __name__ == "__main__": main()
