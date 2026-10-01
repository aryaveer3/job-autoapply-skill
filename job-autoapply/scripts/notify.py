#!/usr/bin/env python3
"""Alert the user when the run needs attention: sound + macOS notification (+ optional phone push).

Usage: notify.py --event otp|captcha|login|limit|approval|question|error|done --msg "text"

Settings (optional) in profile.json -> "notify":
  {"sound": true, "speak": false, "ntfy_topic": "", "quiet_hours": [23, 7]}
Works on macOS (afplay/osascript/say). Elsewhere falls back to Linux sound players or the terminal bell.
"""
import argparse, json, os, platform, shutil, subprocess, sys, urllib.request, datetime as dt
from pathlib import Path

HOME = Path(os.environ.get("JOB_AUTOAPPLY_HOME", Path.home() / "job-autoapply"))
URGENT = {"otp", "captcha", "login", "limit", "error"}          # run is blocked
EVENTS = URGENT | {"approval", "question", "done"}               # waiting / finished
MAC_SOUND = {"urgent": "Sosumi", "waiting": "Glass", "done": "Hero"}
TITLE = {"otp": "OTP needed", "captcha": "CAPTCHA — action needed", "login": "Please log in",
         "limit": "Platform limit / warning", "error": "Run stopped", "approval": "Approve to continue",
         "question": "Question needs your answer", "done": "Job hunt run finished"}

def settings():
    try: return {"sound": True, "speak": False, "ntfy_topic": "", "quiet_hours": None,
                 **json.loads((HOME / "profile.json").read_text()).get("notify", {})}
    except Exception: return {"sound": True, "speak": False, "ntfy_topic": "", "quiet_hours": None}

def quiet(qh):
    if not qh: return False
    h = dt.datetime.now().hour; start, end = qh
    return start <= h or h < end if start > end else start <= h < end

def run(cmd):
    try: subprocess.run(cmd, check=False, timeout=15, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); return True
    except Exception: return False

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--event", required=True, choices=sorted(EVENTS)); ap.add_argument("--msg", default="")
    a = ap.parse_args(); s = settings(); level = "urgent" if a.event in URGENT else ("done" if a.event == "done" else "waiting")
    title = f"Job Autoapply: {TITLE[a.event]}"; msg = (a.msg or TITLE[a.event])[:200]; did = []
    silent = quiet(s.get("quiet_hours")) and level != "urgent"
    if platform.system() == "Darwin":
        snd = MAC_SOUND[level]
        esc = lambda t: t.replace("\\", "\\\\").replace('"', '\\"')
        if run(["osascript", "-e", f'display notification "{esc(msg)}" with title "{esc(title)}"' + ("" if silent or not s["sound"] else f' sound name "{snd}"')]): did.append("banner")
        if s["sound"] and not silent and level == "urgent":
            for _ in range(2): run(["afplay", f"/System/Library/Sounds/{snd}.aiff"])
            did.append("sound")
        elif s["sound"] and not silent: did.append("sound")
        if s.get("speak") and not silent and run(["say", TITLE[a.event]]): did.append("voice")
    elif s["sound"] and not silent:
        for cmd in (["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"], ["spd-say", TITLE[a.event]]):
            if shutil.which(cmd[0]) and run(cmd): did.append("sound"); break
        else:
            sys.stderr.write("\a"); sys.stderr.flush(); did.append("bell")
        if shutil.which("notify-send") and run(["notify-send", title, msg]): did.append("banner")
    topic = s.get("ntfy_topic")
    if topic:
        try:
            req = urllib.request.Request(f"https://ntfy.sh/{topic}", data=msg.encode(), method="POST",
                  headers={"Title": title, "Priority": "high" if level == "urgent" else "default", "Tags": "briefcase"})
            urllib.request.urlopen(req, timeout=10); did.append("phone")
        except Exception as e: did.append(f"phone_failed:{type(e).__name__}")
    HOME.mkdir(parents=True, exist_ok=True)
    with open(HOME / "attention.log", "a") as f:
        f.write(json.dumps({"ts": dt.datetime.now().isoformat(timespec="seconds"), "event": a.event, "msg": msg, "via": did}) + "\n")
    print(json.dumps({"notified": did or ["log_only"], "event": a.event}))

if __name__ == "__main__": main()
