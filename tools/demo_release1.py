"""Release 1 demonstration: run the five checks live, then make a phone-sized video of the run.

  python tools/demo_release1.py run                  # live run against AWS, then the video
  python tools/demo_release1.py run --offline data/  # scenes 1 and 2 only, from the synthetic files
  python tools/demo_release1.py video <run.json>     # make the video again from a saved run

What it does:
  1. Runs real commands, the same ones a reader can type: the customer summary, the register check,
     tests T5a to T5f, an attempt to create storage in Singapore, and a read of one evidence record
     and its lock. Each command's output is shown in the terminal as it runs.
  2. Saves every command, the time it ran and its full output in notes/demo/<date>-<time>/run.json.
  3. Draws the video from that file: each command appears as if typed, then its real output appears,
     with key words in amber. 1080 x 1350 pixels (4:5) with a caption on every scene, no sound.

The typing is drawn afterwards; the commands and outputs are exactly those of the run, and the first
frame says so. Account numbers, the organisation id, policy ids and email addresses are masked. If a
command does not give the expected result, every frame says NOT FOR PUBLISHING.

notes/demo/ is ignored by Git, because the saved outputs contain account ids.
Needs ffmpeg, the DejaVu fonts and the Python package Pillow (Release 1 guide, Step 7).
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import shutil
import string
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
IST = ZoneInfo("Asia/Kolkata")
CUSTOMER = "C-TEST-0001"
WIDTH = 46            # characters per line in the terminal panel

# The scenes: caption tag, legal reference, title, sentence, and the key words shown in amber.
SCENES = {
    "1": ("1 OF 5", "Section 4 · Section 8(1)", "Know what you hold",
          "One command: every kind of personal data held about one customer, its legal basis, how long it is kept.",
          [r"Consent", r"Sec 7\(\w\)", r"XXXX[ X\d]*", r"\d+ categories in \d+ stores"]),
    "2": ("2 OF 5", "Section 4 · Section 8(2)", "No legal basis, no data flow",
          "A new flow sends mobile numbers to a marketing partner. The check refuses it.",
          [r"FAIL \[[^\]]+\]", r"Result: FAIL", r"Result: PASS"]),
    "3": ("3 OF 5", "Rule 6(1)(c) · Rule 6(1)(e)", "Logs that cannot be erased",
          "The most powerful administrator tries six ways to delete or weaken the logs. Each test passes only if AWS refuses.",
          [r"PASSED", r"\d+ passed"]),
    "4": ("4 OF 5", "Design choice · Section 16", "Data stays in Mumbai",
          "An engineer with full rights to build tries to create storage in Singapore.",
          [r"AccessDenied", r"with an explicit deny in a service control policy"]),
    "5": ("5 OF 5", "Rule 6(1)(g)", "Proof that cannot be altered",
          "The record test T5a just wrote, read back from the evidence bucket, and its lock.",
          [r'"outcome": "PASS"', r"COMPLIANCE", r'"RetainUntilDate": "[^"]+"']),
}


# ---------------------------------------------------------------- helpers

def mask(text: str) -> str:
    """Never show account, organisation or policy ids, or email addresses."""
    text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "<email>", str(text))
    text = re.sub(r"\d{12}", "<account-id>", text)
    text = re.sub(r"\bo-[a-z0-9]{10,32}\b", "<org-id>", text)
    return re.sub(r"/p-[a-z0-9]{8,128}", "/<policy-id>", text)


def load_env() -> None:
    """Read config/local.env, as the tests do."""
    f = ROOT / "config" / "local.env"
    if f.exists():
        for line in f.read_text().splitlines():
            line = line.split("#", 1)[0].strip()
            if "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()


def sh(shown: str, actual: str | None = None) -> dict:
    """Run one command in the workbench folder; print and keep its output.
    `shown` is the command as it appears in the video; `actual` is the same command with the full
    path of this Python interpreter, when it differs only in that."""
    t = datetime.now(IST)
    env = dict(os.environ, COLUMNS=str(WIDTH))   # pytest fits its lines to the panel
    p = subprocess.run(["bash", "-c", actual or shown], cwd=ROOT, capture_output=True, text=True, env=env)
    out = "\n".join(ln.rstrip() for ln in (p.stdout + p.stderr).expandtabs(4).strip("\n").splitlines())
    print(f"\n\033[1;96m$ \033[1;97m{mask(shown)}\033[0m\n{mask(out)}")
    return {"time": t.strftime("%H:%M:%S IST"), "cmd": shown, "rc": p.returncode, "out": out}


# ---------------------------------------------------------------- the run

def run(args) -> Path:
    load_env()
    started = datetime.now(IST)
    folder = ROOT / "notes" / "demo" / started.strftime("%Y%m%d-%H%M%S")
    folder.mkdir(parents=True)
    py = sys.executable
    live = not args.offline
    scenes, problems = {}, []

    def need(cond, text):
        if not cond:
            problems.append(text)

    # 1. Customer summary
    src = f"--offline {args.offline}" if not live else f"--profile {os.environ.get('DPDP_PROFILE_WORKLOAD', 'dpdp-workload-eng')}"
    c = f"python tools/customer_summary.py --customer {CUSTOMER} {src} --compact"
    r = sh(c, c.replace("python ", py + " ", 1))
    scenes["1"] = [r]
    need(r["rc"] == 0 and "XXXX" in r["out"] and "categories" in r["out"], "Scene 1: no summary, or Aadhaar and PAN not masked")

    # 2. Register check: the flow without a legal basis, then the approved register
    c1 = "python tools/register_check.py --register tests/fixtures/register_missing_basis.yaml | grep -v WARN"
    c2 = "python tools/register_check.py | tail -1"
    r1, r2 = sh(c1, c1.replace("python ", py + " ", 1)), sh(c2, c2.replace("python ", py + " ", 1))
    scenes["2"] = [r1, r2]
    need("Result: FAIL" in r1["out"], "Scene 2: the flow without a legal basis was not blocked")
    need("Result: PASS" in r2["out"], "Scene 2: the approved register does not pass")

    if live:
        la = os.environ["DPDP_PROFILE_LOGARCHIVE"]
        wl = os.environ.get("DPDP_PROFILE_WORKLOAD", "dpdp-workload-eng")
        evb = os.environ["DPDP_EVIDENCE_LIVE_BUCKET"]

        # 3. Tests T5a to T5f
        c = "python -m pytest --live -q -rp -p no:cacheprovider tests/foundations/test_t5_logs_cannot_be_erased.py"
        r = sh(c, c.replace("python ", py + " ", 1))
        scenes["3"] = [r]
        need(r["rc"] == 0 and re.search(r"\b6 passed\b", r["out"]), "Scene 3: not all six attempts were refused")

        # 4. Storage in Singapore
        name = "dpdp-region-check-" + "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
        c = (f"aws s3api create-bucket --bucket {name} --region ap-southeast-1 "
             f"--create-bucket-configuration LocationConstraint=ap-southeast-1 --profile {wl}")
        r = sh(c)
        if r["rc"] == 0:  # not refused: remove it again at once
            sh(f"aws s3api delete-bucket --bucket {name} --region ap-southeast-1 --profile {wl}")
        scenes["4"] = [r]
        need(r["rc"] != 0 and "AccessDenied" in r["out"], "Scene 4: storage outside Mumbai was not refused")

        # 5. The T5a evidence record just written, and its lock
        find = sh(f"aws s3 ls s3://{evb}/dpdp-log-archive/ --recursive --profile {la} "
                  f"| grep t5a-delete-log-file | sort | tail -1 | awk '{{print $4}}'")
        key = find["out"].strip().splitlines()[-1] if find["out"].strip() else ""
        if key:
            ra = sh(f"aws s3 cp \"s3://{evb}/{key}\" - --profile {la} "
                    f"| grep -E '\"(control|time|outcome|sha256)\"'")
            rb = sh(f"aws s3api get-object-retention --bucket {evb} --key \"{key}\" --profile {la}")
            scenes["5"] = [ra, rb]
            need('"PASS"' in ra["out"] and "COMPLIANCE" in rb["out"], "Scene 5: record not passed, or not in compliance mode")
        else:
            problems.append("Scene 5: no evidence record from test T5a")
    else:
        problems.append("Offline test: scenes 3 to 5 need AWS and were not run")

    data = {"run_at": started.isoformat(timespec="seconds"), "live": live, "scenes": scenes, "problems": problems}
    out = folder / "run.json"
    out.write_text(json.dumps(data, indent=2))
    print()
    for p in problems:
        print(f"\033[1;91m{p}\033[0m")
    print(f"\nResults saved in {out.relative_to(ROOT)}")
    if not args.no_video:
        make_video(out)
    return out


# ---------------------------------------------------------------- the video

def make_video(run_json: Path) -> Path:
    from PIL import Image, ImageDraw, ImageFont

    run_json = Path(run_json).resolve()
    data = json.loads(run_json.read_text())
    if "scenes" not in data:
        sys.exit("This run.json is from the earlier version of the tool. Run the demonstration again.")
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg is not installed. Run: sudo apt install -y ffmpeg")
    fdir = next((Path(p) for p in ("/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/dejavu",
                                   "/Library/Fonts", str(Path.home() / "Library/Fonts"))
                 if (Path(p) / "DejaVuSansMono.ttf").exists()), None)
    if not fdir:
        sys.exit("The DejaVu fonts are not installed. Run: sudo apt install -y fonts-dejavu-core")

    def F(name, size):
        return ImageFont.truetype(str(fdir / name), size)

    W, H = 1080, 1350
    TAG, TITLE, SUB = F("DejaVuSans-Bold.ttf", 30), F("DejaVuSans-Bold.ttf", 56), F("DejaVuSans.ttf", 34)
    MONO, MONOB = F("DejaVuSansMono.ttf", 33), F("DejaVuSansMono-Bold.ttf", 33)
    FOOT, FOOTB, SMALL = F("DejaVuSans.ttf", 24), F("DejaVuSans-Bold.ttf", 24), F("DejaVuSans.ttf", 30)
    BIG1, BIG2, BIG3 = F("DejaVuSans-Bold.ttf", 44), F("DejaVuSans-Bold.ttf", 84), F("DejaVuSans.ttf", 40)
    NAVY, CYAN, WHITE, SOFT, GREY = (7, 13, 24), (26, 207, 223), (245, 247, 250), (190, 202, 216), (150, 156, 166)
    AMBER, RED = (255, 190, 60), (240, 90, 90)
    STY = {"n": ((215, 215, 215), MONO), "b": (WHITE, MONOB), "g": (GREY, MONO), "c": (CYAN, MONOB), "h": (AMBER, MONOB)}
    CW, LH = MONO.getlength("M"), 43
    PX0, PX1, PANEL_BOTTOM = 40, 1040, 1185
    icon_path = ROOT / "tools" / "assets" / "defenaar-icon.png"
    icon = Image.open(icon_path).convert("RGBA") if icon_path.exists() else None
    run_at = datetime.fromisoformat(data["run_at"])
    when = run_at.strftime("%A %d %B %Y, %H:%M IST")
    warning = None
    if data["problems"]:
        warning = "NOT FOR PUBLISHING · " + ("offline test" if not data["live"] else "a check did not pass")

    def wrap_px(d, text, font, width):
        out, cur = [], ""
        for w in text.split():
            t = (cur + " " + w).strip()
            if d.textlength(t, font=font) <= width:
                cur = t
            else:
                out.append(cur)
                cur = w
        return out + [cur]

    def scaled_icon(h):
        return icon.resize((int(icon.width * h / icon.height), h), Image.LANCZOS)

    def footer(im, d):
        x = 50
        if icon:
            ic = scaled_icon(36)
            im.paste(ic, (x, 1264), ic)
            x += ic.width + 12
        d.text((x, 1268), "Rituraj Buddhisagar", font=FOOTB, fill=SOFT)
        x += d.textlength("Rituraj Buddhisagar", font=FOOTB)
        d.text((x, 1268), " · Defenaar Consulting", font=FOOT, fill=GREY)
        t = f"Fernleaf Finance (fictional) · synthetic data · live run {run_at.strftime('%d %b %Y, %H:%M IST')}"
        d.text((50, 1304), t, font=FOOT, fill=GREY)
        if warning:
            d.text(((W - d.textlength(warning, font=FOOTB)) / 2, 1218), warning, font=FOOTB, fill=RED)

    def hard_wrap(text):
        return [text[i:i + WIDTH] for i in range(0, len(text), WIDTH)] or [""]

    def highlighted(line, patterns):
        hot = [False] * len(line)
        for pat in patterns:
            for m in re.finditer(pat, line):
                for k in range(m.start(), m.end()):
                    hot[k] = True
        rows = []
        for start in range(0, max(len(line), 1), WIDTH):
            segs, k, end = [], start, min(start + WIDTH, len(line))
            while k < end:
                j = k
                while j < end and hot[j] == hot[k]:
                    j += 1
                segs.append((line[k:j], "h" if hot[k] else "n"))
                k = j
            rows.append(segs or [("", "n")])
        return rows

    def screen(step, rows, cursor=False):
        tag, ref, title, sub, _ = SCENES[step]
        im = Image.new("RGB", (W, H), NAVY)
        d = ImageDraw.Draw(im)
        d.text((50, 44), tag, font=TAG, fill=CYAN)
        d.text((W - 50 - d.textlength(ref, font=TAG), 44), ref, font=TAG, fill=SOFT)
        y = 92
        for ln in wrap_px(d, title, TITLE, 980):
            d.text((50, y), ln, font=TITLE, fill=WHITE)
            y += 64
        y += 4
        for ln in wrap_px(d, sub, SUB, 980):
            d.text((50, y), ln, font=SUB, fill=SOFT)
            y += 44
        top = y + 20
        d.rounded_rectangle([PX0, top, PX1, PANEL_BOTTOM], radius=18, fill=(12, 12, 12), outline=(34, 48, 66), width=2)
        for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
            d.ellipse([PX0 + 24 + i * 30, top + 20, PX0 + 40 + i * 30, top + 36], fill=c)
        cap = int((PANEL_BOTTOM - top - 70) // LH)
        rows = rows[-cap:]   # scroll like a terminal once the panel is full
        yy, x = top + 60, PX0 + 34
        for line in rows:
            x = PX0 + 34
            for text, st in line:
                col, f = STY[st]
                d.text((x, yy), text, font=f, fill=col)
                x += CW * len(text)
            yy += LH
        if cursor:
            d.rectangle([x + 2, yy - LH + 6, x + 2 + CW * 0.6, yy - 8], fill=WHITE)
        footer(im, d)
        return im, cap

    def card(rows, start=340):
        im = Image.new("RGB", (W, H), NAVY)
        d = ImageDraw.Draw(im)
        d.line([(W / 2 - 80, start - 50), (W / 2 + 80, start - 50)], fill=CYAN, width=6)
        y = start
        for text, font, col, gap in rows:
            for ln in wrap_px(d, text, font, 960):
                d.text(((W - d.textlength(ln, font=font)) / 2, y), ln, font=font, fill=col)
                y += font.size + 20
            y += gap
        footer(im, d)
        return im

    folder = run_json.parent
    frames = folder / "frames"
    shutil.rmtree(frames, ignore_errors=True)
    frames.mkdir()
    seg = []

    def hold(im, sec):
        p = frames / f"f{len(seg):04d}.png"
        im.save(p)
        seg.append((p, sec))

    hold(card([("DPDP IN PRACTICE · RELEASE 1", TAG, CYAN, 20), ("Release 1", BIG2, WHITE, 30),
               ("Five things this system proves, live on AWS", BIG3, SOFT, 40),
               (f"Replayed from a live run on {when}.", SMALL, WHITE, 6),
               ("Commands and AWS responses unchanged; account ids masked; key words in amber.", SMALL, GREY, 0)]), 4.5)

    for step in "12345":
        runs = data["scenes"].get(step)
        if not runs:
            continue
        patterns = SCENES[step][4]
        rows = [[(f"run {runs[0]['time']}", "g")]]
        for k, r in enumerate(runs):
            if k:
                rows.append([("", "n")])
            cmd = hard_wrap("$ " + mask(r["cmd"]))
            done = list(rows)
            # the command, typed: three characters a frame
            text, typed = "".join(cmd), 2
            while typed <= len(text):
                part = text[:typed]
                lines = [part[i:i + WIDTH] for i in range(0, len(part), WIDTH)]
                cur = [[(lines[0][:2], "c"), (lines[0][2:], "b")]] + [[(ln, "b")] for ln in lines[1:]]
                hold(screen(step, done + cur, cursor=True)[0], 0.05)
                if typed == len(text):
                    break
                typed = min(typed + 3, len(text))
            rows = done + [[(cmd[0][:2], "c"), (cmd[0][2:], "b")]] + [[(ln, "b")] for ln in cmd[1:]]
            hold(screen(step, rows, cursor=True)[0], 0.6)
            # the output, line by line, as it came back
            out = []
            for raw in (mask(r["out"]) or "(no output)").splitlines():
                out += highlighted(raw, patterns)
            for i in range(0, len(out), 2):
                rows_now = rows + out[:i + 2]
                hold(screen(step, rows_now)[0], 0.07)
            rows = rows + out
        hold(screen(step, rows)[0], 5.5)

    hold(card([("DPDP IN PRACTICE · RELEASE 1", TAG, CYAN, 20),
               ("Code, tests and guide", BIG3, SOFT, 0), ("github.com/riturajb/dpdp-on-aws", BIG1, WHITE, 40),
               ("Every control traced from the law to the code, the test and the evidence.", BIG3, SOFT, 30),
               ("Not legal advice.", FOOT, GREY, 0)]), 5)

    lst = folder / "frames.txt"
    lst.write_text("".join(f"file '{p}'\nduration {s}\n" for p, s in seg) + f"file '{seg[-1][0]}'\n")
    video = folder / "release1_demo.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "20", "-movflags", "+faststart",
                    str(video)], check=True)
    shutil.rmtree(frames, ignore_errors=True)
    lst.unlink()
    print(f"Video: {os.path.relpath(video, ROOT)} ({round(sum(s for _, s in seg))} seconds)")
    if warning:
        print(f"\033[1;91m{warning}\033[0m")
    return video


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run the checks, then make the video")
    r.add_argument("--offline", help="folder written by generate_synthetic_data.py; scenes 1 and 2 only")
    r.add_argument("--no-video", action="store_true")
    v = sub.add_parser("video", help="make the video again from a saved run")
    v.add_argument("run_json")
    args = ap.parse_args(argv)
    if args.cmd == "run":
        out = run(args)
        return 1 if json.loads(out.read_text())["problems"] else 0
    make_video(Path(args.run_json))
    return 0


if __name__ == "__main__":
    sys.exit(main())
