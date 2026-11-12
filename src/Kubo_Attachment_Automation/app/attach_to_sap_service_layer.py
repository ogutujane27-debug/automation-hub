import os
import csv
import shutil
import logging
import requests
from pathlib import Path

# ============================================================
# KUBO -> SAP ATTACHMENT EXECUTION
#
# Flow:
#   TO_ATTACH
#       ->
#   Resolve SAP DocEntry
#       ->
#   Check U_Attachment
#       ->
#   Copy PDF to SAP attachment share
#       ->
#   PATCH U_Attachment
#       ->
#   Verify
#
# SAP rejection:
#   -> REVIEW
#   -> record error
#   -> continue with next document
#
# IMPORTANT:
#   Matching engine is NOT changed here.
# ============================================================

requests.packages.urllib3.disable_warnings()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORT_FILE = PROJECT_ROOT / "reports" / "attachment_decision_report.csv"
LOG_FILE = PROJECT_ROOT / "logs" / "attachment_execution.log"

_folder = os.environ.get("SAP_ATTACHMENT_FOLDER", "").strip()
if not _folder:
    raise SystemExit(
        "SAP_ATTACHMENT_FOLDER is not set. Set it in run_Kubo.bat to the "
        "attachment folder of the company you are logging into."
    )
SAP_ATTACHMENT_FOLDER = Path(_folder)

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

SL_BASE_URL = os.environ.get("SL_BASE_URL", "")
SL_USER = os.environ.get("SL_USER", "")
SL_PASSWORD = os.environ.get("SL_PASSWORD", "")
SL_COMPANY_DB = os.environ.get("SL_COMPANY_DB", "")


def get_service_layer_session():
    """Login to SAP Service Layer."""
    login_url = f"{SL_BASE_URL}/Login"

    payload = {
        "CompanyDB": SL_COMPANY_DB,
        "UserName": SL_USER,
        "Password": SL_PASSWORD
    }

    try:
        response = requests.post(
            login_url,
            json=payload,
            verify=False,
            timeout=15
        )

        if response.status_code == 200:
            logging.info("Successfully logged into SAP Service Layer.")
            return response.cookies

        logging.error(
            f"Service Layer Login Failed "
            f"({response.status_code}): {response.text}"
        )
        return None

    except Exception as exc:
        logging.error(
            f"Connection error during Service Layer authentication: {exc}"
        )
        return None


def logout_service_layer(session):
    """Logout from SAP Service Layer."""
    if not session:
        return

    try:
        response = requests.post(
            f"{SL_BASE_URL}/Logout",
            cookies=session,
            verify=False,
            timeout=10
        )

        logging.info(
            f"Service Layer logout returned {response.status_code}."
        )

    except Exception as exc:
        logging.error(f"Exception during logout: {exc}")


def get_delivery_note(session, doc_entry):
    """Read the SAP Delivery Note."""
    url = (
        f"{SL_BASE_URL}/DeliveryNotes({doc_entry})"
        "?$select=DocEntry,DocNum,CardName,U_Attachment,AttachmentEntry"
    )

    try:
        response = requests.get(
            url,
            cookies=session,
            verify=False,
            timeout=15
        )

        if response.status_code != 200:
            logging.error(
                f"Could not read DocEntry {doc_entry}: "
                f"{response.status_code} - {response.text}"
            )
            return None

        return response.json()

    except Exception as exc:
        logging.error(
            f"Exception reading DocEntry {doc_entry}: {exc}"
        )
        return None





def verify_already_attached(session, doc_entry):
    """
    Check whether the SAP Delivery Note already has an attachment.

    Checks both:
      - U_Attachment: the attachment field used by our production flow
      - AttachmentEntry: standard SAP attachment reference

    Returns:
        True  = attachment already exists
        False = no attachment
    """
    delivery = get_delivery_note(session, doc_entry)

    if delivery is None:
        return False

    u_attachment = delivery.get("U_Attachment")
    attachment_entry = delivery.get("AttachmentEntry")

    if u_attachment not in (None, ""):
        logging.info(
            f"DocEntry {doc_entry} already has U_Attachment: "
            f"{u_attachment}"
        )
        return True

    if attachment_entry not in (None, "", 0, "0"):
        logging.info(
            f"DocEntry {doc_entry} already has AttachmentEntry "
            f"{attachment_entry}"
        )
        return True

    return False


def upload_attachment(session, pdf_path):
    """
    Upload a PDF through SAP Service Layer /Attachments2.

    Returns:
        Attachment entry number on success
        None on failure
    """

    source = Path(pdf_path)

    if not source.exists():
        logging.error(f"Attachment file does not exist: {source}")
        return None

    if source.suffix.lower() != ".pdf":
        logging.error(f"Attachment is not a PDF: {source}")
        return None

    url = f"{SL_BASE_URL}/Attachments2"

    try:
        with open(source, "rb") as file_handle:
            files = {
                "files": (
                    source.name,
                    file_handle,
                    "application/pdf"
                )
            }

            response = requests.post(
                url,
                files=files,
                cookies=session,
                verify=False,
                timeout=60
            )

        if response.status_code not in (200, 201):
            logging.error(
                f"Attachments2 upload failed for {source}: "
                f"HTTP {response.status_code} - {response.text}"
            )
            return None

        data = response.json()

        atc_entry = (
            data.get("AbsoluteEntry")
            or data.get("AbsEntry")
            or data.get("AtcEntry")
        )

        if atc_entry is None:
            logging.error(
                f"Attachments2 upload succeeded but no attachment "
                f"entry was returned: {response.text}"
            )
            return None

        logging.info(
            f"Attachments2 upload successful: "
            f"{source} -> AttachmentEntry {atc_entry}"
        )

        return atc_entry

    except Exception as exc:
        logging.error(
            f"Exception uploading attachment {source}: {exc}"
        )
        return None


def link_attachment_to_delivery(session, doc_entry, atc_entry):
    """
    Link an SAP attachment entry to a Delivery Note.

    Returns:
        True on success
        False on failure
    """

    url = f"{SL_BASE_URL}/DeliveryNotes({doc_entry})"

    payload = {
        "AttachmentEntry": int(atc_entry)
    }

    try:
        response = requests.patch(
            url,
            json=payload,
            cookies=session,
            verify=False,
            timeout=30
        )

        if response.status_code in (200, 204):
            logging.info(
                f"Attachment {atc_entry} successfully linked "
                f"to Delivery Note DocEntry {doc_entry}"
            )
            return True

        logging.error(
            f"Failed linking attachment {atc_entry} "
            f"to DocEntry {doc_entry}: "
            f"HTTP {response.status_code} - {response.text}"
        )

        return False

    except Exception as exc:
        logging.error(
            f"Exception linking attachment {atc_entry} "
            f"to DocEntry {doc_entry}: {exc}"
        )
        return False

def copy_pdf_to_sap_share(pdf_path):
    """
    Copy Kubo PDF into SAP's configured attachment folder.

    Returns:
        destination Path on success
        None on failure
    """

    source = Path(pdf_path)

    if not source.exists():
        logging.error(f"Source PDF does not exist: {source}")
        return None

    try:
        SAP_ATTACHMENT_FOLDER.mkdir(parents=True, exist_ok=True)

        destination = SAP_ATTACHMENT_FOLDER / source.name

        # If the exact file already exists, do not overwrite it.
        if destination.exists():
            source_size = source.stat().st_size
            destination_size = destination.stat().st_size

            if source_size != destination_size:
                logging.error(
                    f"Existing SAP attachment has different size: "
                    f"{destination}"
                )
                return None

            logging.info(
                f"Attachment file already exists in SAP share: "
                f"{destination}"
            )
            return destination

        shutil.copy2(source, destination)

        logging.info(
            f"Copied PDF to SAP attachment share: "
            f"{source} -> {destination}"
        )

        return destination

    except Exception as exc:
        logging.error(
            f"Exception copying PDF to SAP share "
            f"{source}: {exc}"
        )
        return None


def to_link(path):
    """Text written into SAP. KUBO_LINK_PREFIX lets a Linux server write the Windows share path."""
    prefix = os.environ.get("KUBO_LINK_PREFIX", "").strip()
    p = Path(str(path))
    if prefix and p.parent == Path(str(SAP_ATTACHMENT_FOLDER)):
        return prefix.replace("/", "\\").rstrip("\\") + "\\" + p.name
    return str(path)


def update_u_attachment(session, doc_entry, attachment_path):
    """Update the custom U_Attachment field."""

    url = f"{SL_BASE_URL}/DeliveryNotes({doc_entry})"

    payload = {
        "U_Attachment": to_link(attachment_path)
    }

    try:
        response = requests.patch(
            url,
            json=payload,
            cookies=session,
            verify=False,
            timeout=20
        )

        if response.status_code == 204:
            logging.info(
                f"U_Attachment successfully updated "
                f"for DocEntry {doc_entry}: {attachment_path}"
            )
            return True, ""

        error_text = response.text

        logging.error(
            f"SAP rejected U_Attachment update for "
            f"DocEntry {doc_entry}: "
            f"HTTP {response.status_code} - {error_text}"
        )

        return False, error_text

    except Exception as exc:
        logging.error(
            f"Exception updating U_Attachment "
            f"for DocEntry {doc_entry}: {exc}"
        )
        return False, str(exc)


def verify_u_attachment(session, doc_entry, expected_path):
    """Verify SAP contains the exact attachment path."""

    url = (
        f"{SL_BASE_URL}/DeliveryNotes({doc_entry})"
        "?$select=DocEntry,DocNum,U_Attachment"
    )

    try:
        response = requests.get(
            url,
            cookies=session,
            verify=False,
            timeout=15
        )

        if response.status_code != 200:
            logging.error(
                f"Verification failed for DocEntry {doc_entry}: "
                f"{response.status_code} - {response.text}"
            )
            return False

        actual_path = response.json().get("U_Attachment")

        if actual_path == to_link(expected_path):
            logging.info(
                f"VERIFIED attachment for DocEntry {doc_entry}: "
                f"{actual_path}"
            )
            return True

        logging.error(
            f"Attachment verification mismatch for "
            f"DocEntry {doc_entry}. "
            f"Expected: {expected_path} | "
            f"Actual: {actual_path}"
        )
        return False

    except Exception as exc:
        logging.error(
            f"Exception verifying DocEntry {doc_entry}: {exc}"
        )
        return False


def update_report_row(row, status, error=""):
    """Update in-memory report row."""

    row["Status"] = status

    if error:
        import re as _re
        m = _re.search(r'"value"\s*:\s*"([^"]+)"', str(error))
        row["Reason"] = ("SAP rejected: " + m.group(1)) if m else " ".join(str(error).split())[:300]

    return row



def get_doc_entry_by_docnum(session, doc_num):
    try:
        res = requests.get(f"{SL_BASE_URL}/DeliveryNotes?%24filter=DocNum eq {int(str(doc_num).strip())}&%24select=DocEntry", cookies=session, verify=False, timeout=15)
        if res.status_code == 200:
            m = res.json().get('value', [])
            if m and len(m) > 0: return m[0].get('DocEntry'); return None
        return None
    except Exception as e: logging.error(f"LIVE LOOKUP ERROR: {str(e)}"); return None

def run_attachment_pipeline():

    if not REPORT_FILE.exists():
        print(
            "No decision report found. "
            "Run Kubo_Attachment_Automation.py first."
        )
        return

    session = get_service_layer_session()

    if not session:
        print("Could not connect to SAP Service Layer.")
        return

    success_count = 0
    already_attached_count = 0
    review_count = 0
    lookup_failed_count = 0

    rows = []

    try:
        with open(
            REPORT_FILE,
            mode="r",
            encoding="utf-8-sig",
            newline=""
        ) as f:

            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []

            for row in reader:

                if row.get("Status") != "TO_ATTACH":
                    rows.append(row)
                    continue

                only = os.environ.get("KUBO_ONLY_DOCNUM", "").strip()
                if only and (row.get("SAP_DocNum") or "").strip() not in [x.strip() for x in only.split(",")]:
                    rows.append(row)
                    continue

                doc_num = row.get("SAP_DocNum")
                pdf_path = row.get("FilePath")

                import json as _json, time as _time
                _hours = float(os.environ.get("KUBO_REFUSAL_RETRY_HOURS", "24") or 24)
                _mem_path = Path(__file__).resolve().parent.parent / "refused_memory.json"
                try:
                    _mem = _json.loads(_mem_path.read_text(encoding="utf-8")) if _mem_path.exists() else {}
                except Exception:
                    _mem = {}
                _hit = _mem.get(str(doc_num))
                if _hit and _hours > 0 and _time.time() - _hit.get("ts", 0) < _hours * 3600:
                    row["Status"] = "REVIEW"
                    row["Reason"] = "SAP rejected earlier, not retried until " + _time.strftime("%d %b %H:%M", _time.localtime(_hit["ts"] + _hours * 3600))
                    rows.append(row)
                    continue

                if not doc_num or not pdf_path:
                    logging.warning(
                        f"Missing SAP_DocNum or FilePath: {row}"
                    )
                    row = update_report_row(
                        row,
                        "REVIEW",
                        "Missing SAP_DocNum or FilePath"
                    )
                    review_count += 1
                    rows.append(row)
                    continue

                # ------------------------------------------------
                # 1. Resolve DocEntry
                # ------------------------------------------------

                doc_entry = get_doc_entry_by_docnum(
                    session,
                    doc_num
                )

                if not doc_entry:
                    row = update_report_row(
                        row,
                        "REVIEW",
                        "SAP DocEntry lookup failed"
                    )
                    lookup_failed_count += 1
                    rows.append(row)
                    continue

                # ------------------------------------------------
                # 2. Read SAP Delivery Note
                # ------------------------------------------------

                delivery = get_delivery_note(
                    session,
                    doc_entry
                )

                if delivery is None:
                    row = update_report_row(
                        row,
                        "REVIEW",
                        "Could not read SAP Delivery Note"
                    )
                    review_count += 1
                    rows.append(row)
                    continue

                existing_attachment = verify_already_attached(session, doc_entry)

                # ------------------------------------------------
                # 3. Duplicate protection
                # ------------------------------------------------

                if existing_attachment:
                    logging.info(
                        f"SKIP DocNum {doc_num}: "
                        f"U_Attachment already contains "
                        f"{existing_attachment}"
                    )

                    row = update_report_row(
                        row,
                        "SKIP",
                        "U_Attachment already populated"
                    )

                    already_attached_count += 1
                    rows.append(row)
                    continue

                # ------------------------------------------------
                # 4. Copy PDF to SAP attachment share
                # ------------------------------------------------

                if os.environ.get("KUBO_LINK_ONLY", "0") == "1":
                    _pre_existing = True  # never delete Kubo's original file
                    destination = str(pdf_path)
                else:
                    _f = str(SAP_ATTACHMENT_FOLDER)
                    if _f.startswith("\\") and not _f.startswith("\\\\"):
                        raise SystemExit("SAP_ATTACHMENT_FOLDER looks like a broken UNC path: " + _f)
                    _pre_existing = (SAP_ATTACHMENT_FOLDER / Path(pdf_path).name).exists()
                    if os.environ.get("KUBO_NO_COPY", "0") == "1":
                        _pre_existing = True  # never delete anything in the share
                        _dest = SAP_ATTACHMENT_FOLDER / Path(pdf_path).name
                        if _dest.exists() and _dest.stat().st_size == Path(pdf_path).stat().st_size:
                            destination = _dest
                        else:
                            logging.error(f"NO_COPY: no identical file in the SAP share for {Path(pdf_path).name}")
                            destination = None
                    else:
                        destination = copy_pdf_to_sap_share(
                            pdf_path
                        )

                if destination is None:
                    row = update_report_row(
                        row,
                        "REVIEW",
                        "Could not copy PDF to SAP attachment share"
                    )
                    review_count += 1
                    rows.append(row)
                    continue

                # ------------------------------------------------
                # 5. Update U_Attachment
                # ------------------------------------------------

                success, error = update_u_attachment(
                    session,
                    doc_entry,
                    destination
                )

                if not success:
                    # IMPORTANT:
                    # SAP rejection becomes REVIEW.
                    # Processing continues.
                    try:
                        import json as _json, time as _time
                        _mem_path = Path(__file__).resolve().parent.parent / "refused_memory.json"
                        _mem = _json.loads(_mem_path.read_text(encoding="utf-8")) if _mem_path.exists() else {}
                        _mem[str(doc_num)] = {"ts": _time.time()}
                        _mem_path.write_text(_json.dumps(_mem), encoding="utf-8")
                    except Exception as exc:
                        logging.error(f"Could not save refusal memory: {exc}")
                    if not _pre_existing and destination is not None:
                        try:
                            Path(destination).unlink()
                        except Exception as exc:
                            logging.error(f"Could not remove orphan copy {destination}: {exc}")
                    row = update_report_row(
                        row,
                        "REVIEW",
                        f"SAP rejected attachment: {error}"
                    )

                    review_count += 1
                    rows.append(row)
                    continue

                # ------------------------------------------------
                # 6. Verify
                # ------------------------------------------------

                verified = verify_u_attachment(
                    session,
                    doc_entry,
                    destination
                )

                if not verified:
                    row = update_report_row(
                        row,
                        "REVIEW",
                        "SAP update succeeded but verification failed"
                    )

                    review_count += 1
                    rows.append(row)
                    continue

                # ------------------------------------------------
                # 7. SUCCESS
                # ------------------------------------------------

                row = update_report_row(
                    row,
                    "ATTACHED",
                    "Successfully attached and verified"
                )

                success_count += 1
                rows.append(row)

                print(
                    f"ATTACHED: {doc_num} -> {destination}"
                )

    finally:
        logout_service_layer(session)

    # ------------------------------------------------------------
    # Rewrite report with execution results
    # ------------------------------------------------------------

    if rows:
        try:
            with open(
                REPORT_FILE,
                mode="w",
                encoding="utf-8-sig",
                newline=""
            ) as f:

                writer = csv.DictWriter(
                    f,
                    fieldnames=fieldnames,
                    extrasaction="ignore"
                )

                writer.writeheader()
                writer.writerows(rows)

        except Exception as exc:
            logging.error(
                f"Could not update decision report: {exc}"
            )
            print(
                f"WARNING: Could not update report: {exc}"
            )

    print()
    print("=" * 60)
    print("ATTACHMENT EXECUTION COMPLETE")
    print("=" * 60)
    print(f"Successfully attached : {success_count}")
    print(f"Already attached       : {already_attached_count}")
    print(f"Review                  : {review_count}")
    print(f"Lookup failures         : {lookup_failed_count}")
    print("=" * 60)


if __name__ == "__main__":
    run_attachment_pipeline()

