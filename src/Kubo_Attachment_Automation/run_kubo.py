import os
import re
import csv
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

BASE = Path(__file__).resolve().parent
load_dotenv(BASE / ".env")
sys.path.insert(0, str(BASE))
from mailer import send_mail

LOCK = BASE / "run_kubo.lock"
LOG = BASE / "logs" / "run_kubo_summary.log"
LAST_ERR = BASE / "last_error.txt"
REPORT = BASE / "reports" / "attachment_decision_report.csv"
MAX_LOCK_AGE = 2 * 3600


def num(pattern, text):
    m = re.search(pattern, text)
    return int(m.group(1)) if m else None


def fetch_trucks(docnums):
    out = {}
    docnums = [str(d) for d in docnums if d]
    if not docnums:
        return out
    try:
        import requests, urllib3
        urllib3.disable_warnings()
        url = os.environ["SL_BASE_URL"]
        sess = requests.Session()
        sess.verify = False
        r = sess.post(url + "/Login", json={"CompanyDB": os.environ["SL_COMPANY_DB"], "UserName": os.environ["SL_USER"], "Password": os.environ["SL_PASSWORD"]}, timeout=30)
        r.raise_for_status()
        flt = " or ".join(f"DocNum eq {d}" for d in docnums)
        r = sess.get(url + "/DeliveryNotes?$filter=" + flt + "&$select=DocNum,U_TruckNo,VehiclePlate&$top=100", timeout=60)
        for d in r.json().get("value", []):
            out[str(d["DocNum"])] = f"{d.get('U_TruckNo') or '-'} / {d.get('VehiclePlate') or '-'}"
        sess.post(url + "/Logout", timeout=30)
    except Exception as e:
        out["_error"] = str(e)[:100]
    return out


def refused_lines(rows):
    trucks = fetch_trucks([r.get("SAP_DocNum") for r in rows])
    return [f"{r.get('SAP_DocNum')} | truck: {trucks.get(str(r.get('SAP_DocNum')), '?')} | {r.get('Filename')} | {r.get('Reason')}" for r in rows]


def main():
    if LOCK.exists() and time.time() - LOCK.stat().st_mtime < MAX_LOCK_AGE:
        print("Previous run still in progress, skipping.")
        return 0
    LOCK.write_text("")

    start = datetime.now()
    errors = []
    ta = sk = rv = att = ref = lf = None
    try:
        p = subprocess.run(
            [sys.executable, str(BASE / "app" / "Kubo_Attachment_Automation.py")],
            capture_output=True, text=True, cwd=str(BASE), timeout=900)
        out = (p.stdout or "") + (p.stderr or "")
        ta = num(r"TO_ATTACH\s*:\s*(\d+)", out)
        sk = num(r"SKIP\s*:\s*(\d+)", out)
        rv = num(r"REVIEW\s*:\s*(\d+)", out)
        att = num(r"Successfully attached\s*:\s*(\d+)", out)
        ref = num(r"Review\s*:\s*(\d+)", out)
        lf = num(r"Lookup failures\s*:\s*(\d+)", out)
        if p.returncode != 0 or ta is None:
            errors.append("Kubo run failed:\n" + out[-600:])
        elif os.environ.get("KUBO_ATTACH") == "1" and att is None:
            errors.append("Attachment step did not complete (Service Layer login failed?):\n" + out[-600:])
    except Exception as e:
        errors.append(f"Run error: {e}")
    finally:
        LOCK.unlink(missing_ok=True)

    refused_rows = []
    if REPORT.exists():
        with open(REPORT, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                if (r.get("Reason") or "").startswith("SAP rejected"):
                    refused_rows.append(r)

    mode = "attach ON" if os.environ.get("KUBO_ATTACH") == "1" else "read-only"
    only = os.environ.get("KUBO_ONLY_DOCNUM", "").strip()
    if only:
        mode += f" (limited to {only})"
    status = "ERRORS" if errors else "OK"
    summary = (f"{start:%Y-%m-%d %H:%M} | {mode} | to_attach={ta} skip={sk} no_number={rv} | "
               f"attached={att} refused={ref} lookup_failed={lf} | {status}")
    print(summary)
    for e in errors:
        print(e)
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(summary + "\n")
        for e in errors:
            f.write(e + "\n")

    subject = None
    if errors:
        subject = "KUBO automation: ERRORS"
    elif att:
        subject = f"KUBO automation: {att} attachment(s) added in SAP"
    sig = "\n".join(e[:200] for e in errors)
    if errors:
        prev = LAST_ERR.read_text(encoding="utf-8") if LAST_ERR.exists() else None
        if prev == sig:
            subject = None  # same failure as last time, do not email again
        else:
            LAST_ERR.write_text(sig, encoding="utf-8")
    elif LAST_ERR.exists():
        LAST_ERR.unlink()
    if subject:
        body = summary
        if errors:
            body += "\n\n" + "\n\n".join(errors)
        if refused_rows:
            body += "\n\nSAP refused these:\n" + "\n".join(refused_lines(refused_rows)[:40])
        try:
            send_mail(subject, body)
        except Exception as e:
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(f"Email failed: {e}\n")
    DIGEST = BASE / "last_digest.txt"
    today = datetime.now().strftime("%Y-%m-%d")
    last = DIGEST.read_text(encoding="utf-8").strip() if DIGEST.exists() else ""
    if refused_rows and not errors and last != today and datetime.now().hour >= 8:
        try:
            lines = refused_lines(refused_rows)
            text = "Still refused by SAP:\n\n" + "\n".join(lines)
            print(text)
            send_mail(f"KUBO daily digest: {len(refused_rows)} deliveries still refused by SAP", text)
            DIGEST.write_text(today, encoding="utf-8")
        except Exception as e:
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(f"Digest failed: {e}\n")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
