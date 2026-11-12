from dotenv import load_dotenv
from pathlib import Path as _Path
load_dotenv(_Path(__file__).resolve().parent.parent / ".env")
from attach_to_sap_service_layer import run_attachment_pipeline
from pathlib import Path
import os
import re
import csv


# ============================================================
# KUBO -> SAP ATTACHMENT AUTOMATION
#
# CURRENT STAGE
#   Kubo PDF files
#       ->
#   Extract delivery number
#       ->
#   George's SQL result
#       ->
#   Match against SAP DocNum
#       ->
#   TO_ATTACH / SKIP / REVIEW
#
# FUTURE STAGE
#   TO_ATTACH
#       ->
#   Attach PDF to SAP Delivery Note
#       ->
#   Verify attachment
#
# IMPORTANT:
#   - Kubo source files are never modified.
#   - George's SQL is the SAP source-of-truth query.
#   - No SAP attachment is performed by this version yet.
# ============================================================


# ============================================================
# GEORGE'S SQL
# ============================================================
#
# This is George's exact SQL.
#
# It is currently expected to be run in SAP B1 Query Manager
# and its result exported as CSV.
#
# Later, when the approved SAP integration method is available,
# this same query/result structure will be connected directly
# to SAP from this program.
# ============================================================

GEORGE_SQL = """
SELECT
    T0."DocNum",
    TO_VARCHAR(T0."DocDate", 'YYYY') AS "Year",
    UPPER(LEFT(MONTHNAME(T0."DocDate"), 3)) AS "Month",
    TO_VARCHAR(T0."DocDate", 'DD/MM/YY') AS "DocDate",
    T0."CardName",
    T0."U_Attachment" AS "Attachment"
FROM "ODLN" T0
WHERE
    T0."U_Attachment" IS NULL
    AND YEAR(T0."DocDate") >= 2025;
"""


# ============================================================
# HANA CONNECTION (LIVE SAP SOURCE)
# ============================================================
#
# Credentials are read from environment variables, NOT hardcoded
# here. This file has previously ended up committed to a personal
# GitHub repo by accident — hardcoding real host/user/password
# here would leak them again if that happens a second time.
#
# On the machine that runs this script, set these once via
# Windows environment variables (System Properties -> Environment
# Variables, or `setx HANA_HOST "..."` in an admin terminal) and
# they persist across runs without ever living in this file:
#
#   HANA_HOST       e.g. 10.0.x.x
#   HANA_PORT       e.g. 30015
#   HANA_USER
#   HANA_PASSWORD
#   HANA_DATABASE   the SAP B1 company SCHEMA to use on this
#                   server (this HANA instance hosts multiple
#                   companies as separate schemas, e.g. "MIK01"
#                   for MIKA, "IAL01_DEV" for another company's
#                   dev copy). This is NOT an MDC tenant name —
#                   it's applied as currentSchema on connect.
#
# Until these are set, DATA_SOURCE below stays "CSV" and the
# script keeps using George's manual export exactly as before.
# ============================================================

HANA_CONFIG = {
    "address": os.environ.get("HANA_HOST", ""),
    "port": int(os.environ.get("HANA_PORT", "30015")),
    "user": os.environ.get("HANA_USER", ""),
    "password": os.environ.get("HANA_PASSWORD", ""),
    "database": os.environ.get("HANA_DATABASE", "NDB"),
    "schema": os.environ.get("HANA_SCHEMA", "IAL01"),
}

# "CSV"  -> always use George's manual SAP B1 Query Manager export,
#           never attempt HANA (use this until credentials arrive)
# "HANA" -> always use the live HANA query, no fallback — use this
#           when specifically testing HANA stability (Test 5/6), so
#           a real failure isn't silently masked by falling back
# "AUTO" -> try HANA first; if it fails for any reason, log why and
#           fall back to CSV automatically (the eventual daily-run mode)
DATA_SOURCE = os.environ.get("DATA_SOURCE", "AUTO")



# ============================================================
# RUN LOG
# ============================================================
#
# Kubo's daily run is launched via run_kubo.bat, likely without
# anyone watching the console. A HANA failure that only prints to
# a console no one sees is the same as a failure that's invisible.
# This writes a timestamped line to a log file every run instead.
# ============================================================

LOG_FILE = None  # set below, after PROJECT_FOLDER is defined


def log_message(message):
    """Append a timestamped line to run_log.txt and also print it."""

    from datetime import datetime

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"

    print(line)

    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(line + "\n")


# ============================================================
# PATHS
# ============================================================

# Kubo downloads deliveries into a subfolder per year/month under
# this base path, e.g. ...\2026\AUGUST, ...\2026\SEPTEMBER, etc.
# The script picks the CURRENT month's subfolder automatically
# every run, so nothing needs editing when the month changes.
KUBO_BASE_FOLDER = Path(os.environ.get(
    "KUBO_BASE_FOLDER",
    r"\\your-server-ip\B1_Shr\Attachments\Acknowledged Deliveries"
))

# Optional testing override, e.g. set once via:
#   setx KUBO_MONTH_OVERRIDE "2026-08"
# Format: "YYYY-MM". Leave unset for normal operation — the
# script then always uses today's actual year/month.
KUBO_MONTH_OVERRIDE = os.environ.get("KUBO_MONTH_OVERRIDE", "")


def resolve_kubo_folder():
    """
    Build the path to the current month's Kubo delivery folder.

    Normally uses the standard English month name. If that exact
    folder does not exist, search the year folder for a folder whose
    name matches the month name after normalizing spelling/case.
    This allows the automation to work with existing Kubo folder
    naming variations without changing the matching engine.
    """
    from datetime import datetime

    if KUBO_MONTH_OVERRIDE:
        try:
            year_str, month_str = KUBO_MONTH_OVERRIDE.split("-")
            year = int(year_str)
            month_number = int(month_str)
        except (ValueError, IndexError) as exc:
            raise ValueError(
                f"KUBO_MONTH_OVERRIDE is set to {KUBO_MONTH_OVERRIDE!r}, "
                "expected format \"YYYY-MM\", e.g. \"2026-08\"."
            ) from exc

        reference_date = datetime(year, month_number, 1)
    else:
        reference_date = datetime.now()

    year_folder = reference_date.strftime("%Y")
    month_folder = reference_date.strftime("%B").upper()

    year_path = KUBO_BASE_FOLDER / year_folder
    expected_path = year_path / month_folder

    if expected_path.exists():
        return expected_path

    # Kubo may contain an existing folder with a spelling variation.
    # Compare normalized names while ignoring spaces and punctuation.
    normalized_expected = (
        month_folder.replace(" ", "").replace("-", "").upper()
    )

    if year_path.exists():
        for candidate in year_path.iterdir():
            if not candidate.is_dir():
                continue

            normalized_candidate = (
                candidate.name.replace(" ", "").replace("-", "").upper()
            )

            # Exact normalized match first.
            if normalized_candidate == normalized_expected:
                return candidate

            # For known folder spelling variations, allow the month
            # name to be recognizable by most of its characters.
            if month_folder == "SEPTEMBER":
                if normalized_candidate == "SEPEMBER":
                    return candidate

    # Preserve the original behavior: return the expected path so
    # scan_kubo_folder() produces the normal clear error if missing.
    return expected_path


KUBO_FOLDER = resolve_kubo_folder()

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# George's SQL result exported from SAP B1 Query Manager.
# Kept in the same project folder as this script.
SAP_EXPORT_FILE = PROJECT_ROOT / "data" / "Delivery Note with No Attachments.csv"

OUTPUT_FILE = PROJECT_ROOT / "reports" / "attachment_decision_report.csv"

LOG_FILE = PROJECT_ROOT / "logs" / "run_log.txt"


# ============================================================
# KUBO SIDE
# ============================================================

def extract_delivery_number(filename):
    """
    Extract the first 8 digits from the beginning of the filename.

    Examples:

        21100978.pdf
            -> 21100978

        25218865-3.pdf
            -> 25218865

        26100907 - CUSTOMER.pdf
            -> 26100907

    Files without a safe 8-digit prefix are REVIEW.
    """

    match = re.match(r"^(\d{8})(?:\D|$)", filename)

    if match:
        return match.group(1)

    return None


def scan_kubo_folder():
    """
    Scan the Kubo network folder.

    Source PDFs are only read.
    They are never renamed, moved, deleted or modified.
    """

    if not KUBO_FOLDER.exists():
        raise FileNotFoundError(
            f"Kubo folder cannot be accessed:\n{KUBO_FOLDER}"
        )

    results = []

    for file_path in KUBO_FOLDER.iterdir():

        if not file_path.is_file():
            continue

        if file_path.suffix.lower() != ".pdf":
            continue

        filename = file_path.name

        delivery_number = extract_delivery_number(filename)

        if delivery_number is None:

            results.append({
                "Filename": filename,
                "FilePath": str(file_path),
                "DeliveryNumber": "",
                "SAP_DocNum": "",
                "SAP_CardName": "",
                "SAP_DocDate": "",
                "Status": "REVIEW",
                "Reason": (
                    "No safe 8-digit delivery number "
                    "at start of filename"
                )
            })

        else:

            results.append({
                "Filename": filename,
                "FilePath": str(file_path),
                "DeliveryNumber": delivery_number,
                "SAP_DocNum": "",
                "SAP_CardName": "",
                "SAP_DocDate": "",
                "Status": "WAITING_FOR_SAP",
                "Reason": ""
            })

    return results


# ============================================================
# SAP SIDE
# ============================================================

def load_pending_delivery_notes():
    """
    Load the result of George's SQL from CSV.

    George's real export (SAP B1 Query Manager -> Save As CSV) is
    NOT a plain comma-separated file:

      - Fields are separated by semicolons (;), not commas.
      - The first column is an unlabeled row-index column.
      - DocNum is exported as text WITH thousands-separator commas,
        e.g. "24,108,312" instead of 24108312.
      - Fields are padded with extra whitespace.

    This function strips all of that so DocNum ends up as a clean
    8-digit string that lines up with Kubo's extracted delivery number.

    Expected columns (after the leading index column):

        DocNum
        Year
        Month
        DocDate
        CardName
        Attachment

    Because George's SQL filters:

        U_Attachment IS NULL

    every record in this file represents a delivery note
    that is currently pending attachment.
    """

    if not SAP_EXPORT_FILE.exists():

        raise FileNotFoundError(
            f"\nSAP export file not found:\n"
            f"{SAP_EXPORT_FILE}\n\n"
            "Expected process:\n"
            "1. Run George's SQL in SAP B1 Query Manager.\n"
            "2. Export the result as CSV.\n"
            "3. Save it to the path above."
        )

    pending = {}

    with SAP_EXPORT_FILE.open(
        "r",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        reader = csv.DictReader(file, delimiter=";")

        # Normalize header names (strip whitespace)
        reader.fieldnames = [
            (name or "").strip() for name in reader.fieldnames
        ]

        required_columns = {
            "DocNum",
            "CardName",
            "DocDate"
        }

        found_columns = set(reader.fieldnames or [])

        missing_columns = required_columns - found_columns

        if missing_columns:

            raise ValueError(
                f"SAP export is missing expected columns: "
                f"{missing_columns}\n"
                f"Found columns: {reader.fieldnames}"
            )

        for row in reader:

            raw_doc_num = row.get("DocNum", "") or ""

            # Strip whitespace and thousands-separator commas:
            # "24,108,312" -> "24108312"
            doc_num = raw_doc_num.strip().replace(",", "")

            if not doc_num:
                continue

            pending[doc_num] = {
                "DocNum": doc_num,
                "CardName": (row.get("CardName", "") or "").strip(),
                "DocDate": (row.get("DocDate", "") or "").strip()
            }

    return pending


def load_pending_delivery_notes_from_hana():
    """
    Run GEORGE_SQL directly against HANA and build the same
    {DocNum: {...}} structure as load_pending_delivery_notes(),
    so the rest of the script (matching, report) doesn't care
    which source was used.

    Requires the hdbcli package:
        pip install hdbcli

    Requires HANA_CONFIG above to be filled in via environment
    variables (HANA_HOST / HANA_PORT / HANA_USER / HANA_PASSWORD
    / optionally HANA_DATABASE — used as the company SCHEMA here).
    """

    missing = [
        key for key in ("address", "user", "password")
        if not HANA_CONFIG[key]
    ]

    if missing:
        raise ValueError(
            "HANA_CONFIG is missing: "
            f"{', '.join(missing)}. "
            "Set the corresponding HANA_HOST / HANA_USER / "
            "HANA_PASSWORD environment variables, or set "
            "DATA_SOURCE back to \"CSV\" until they're available."
        )

    try:
        from hdbcli import dbapi
    except ImportError as exc:
        raise ImportError(
            "hdbcli is not installed. Run: pip install hdbcli"
        ) from exc

    connect_kwargs = {
        "address": HANA_CONFIG["address"],
        "port": HANA_CONFIG["port"],
        "user": HANA_CONFIG["user"],
        "password": HANA_CONFIG["password"],
    }

    # This server hosts multiple SAP B1 companies as separate
    # schemas under one tenant (confirmed via OADM lookup: e.g.
    # "MIK01" = MIKA, "IAL01_DEV" = another company's dev copy).
    # Select the schema with currentSchema — NOT databaseName,
    # which is for a different mechanism (MDC tenant redirect)
    # and is what caused the earlier "not connected" errors.
    if HANA_CONFIG["schema"]:
        connect_kwargs["currentSchema"] = HANA_CONFIG["schema"]

    print("\nHANA CONNECTION DETAILS")
    print("-" * 30)
    print("Host     :", connect_kwargs["address"])
    print("Port     :", connect_kwargs["port"])
    print("User     :", connect_kwargs["user"])
    print("Schema   :", connect_kwargs.get("currentSchema", "[not specified]"))
    print("Password : [hidden]")

    connection = dbapi.connect(**connect_kwargs)

    try:
        cursor = connection.cursor()
        cursor.execute(GEORGE_SQL)

        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()

        cursor.close()
    finally:
        connection.close()

    # Validate columns (same required set as the CSV path). If
    # George's SQL changes upstream, fail loudly here rather than
    # silently returning rows keyed on missing/renamed fields.
    required_columns = {"DocNum", "CardName", "DocDate"}
    found_columns = set(columns)
    missing_columns = required_columns - found_columns

    if missing_columns:
        raise ValueError(
            f"HANA query result is missing expected columns: "
            f"{missing_columns}\n"
            f"Found columns: {columns}"
        )

    pending = {}

    for raw_row in rows:

        record = dict(zip(columns, raw_row))

        raw_doc_num = record.get("DocNum", "")

        doc_num = str(raw_doc_num).strip().replace(",", "")

        if not doc_num:
            continue

        # Match the CSV path's 8-digit zero-padded key so both
        # sources line up identically with Kubo's extracted
        # delivery number.
        doc_num = doc_num.zfill(8)

        pending[doc_num] = {
            "DocNum": doc_num,
            "CardName": (record.get("CardName") or "").strip(),
            "DocDate": (record.get("DocDate") or "").strip()
        }

    return pending


# ============================================================
# SOURCE SELECTION (matches the try-HANA / fallback-CSV design)
# ============================================================

def get_pending_delivery_notes():
    """
    Resolve which SAP source to use for this run, per DATA_SOURCE:

        "CSV"  -> George's manual export only
        "HANA" -> live HANA only, no fallback (errors propagate)
        "AUTO" -> try HANA; on any failure, log the reason and
                  fall back to CSV automatically

    Returns (pending_sap, source_used).
    """

    if DATA_SOURCE == "CSV":
        log_message("Data source: CSV (forced)")
        return load_pending_delivery_notes(), "CSV"

    if DATA_SOURCE == "HANA":
        log_message("Data source: HANA (forced, no fallback)")
        return load_pending_delivery_notes_from_hana(), "HANA"

    if DATA_SOURCE == "AUTO":
        log_message("Data source: AUTO — trying HANA first")
        try:
            pending = load_pending_delivery_notes_from_hana()
            log_message("HANA succeeded.")
            return pending, "HANA"
        except Exception as exc:
            log_message(
                f"HANA failed, falling back to CSV. Reason: {exc}"
            )
            return load_pending_delivery_notes(), "CSV"

    raise ValueError(
        f"Unknown DATA_SOURCE: {DATA_SOURCE!r}. "
        "Expected \"CSV\", \"HANA\", or \"AUTO\"."
    )


# ============================================================
# MATCHING ENGINE
# ============================================================

def match_kubo_to_sap(results, pending_sap):
    """
    Match each Kubo delivery number against the pending
    delivery notes returned by George's SQL.
    """

    for row in results:

        delivery_number = row["DeliveryNumber"]

        # Filename could not be safely matched.
        if not delivery_number:
            continue

        # Delivery exists in George's pending list.
        if delivery_number in pending_sap:

            sap = pending_sap[delivery_number]

            row["SAP_DocNum"] = sap["DocNum"]

            row["SAP_CardName"] = sap["CardName"]

            row["SAP_DocDate"] = sap["DocDate"]

            row["Status"] = "TO_ATTACH"

            row["Reason"] = (
                "Kubo delivery number matches SAP DocNum "
                "returned by George's SQL where "
                "U_Attachment IS NULL"
            )

        else:

            row["Status"] = "SKIP"

            row["Reason"] = (
                "Delivery number is not present in "
                "George's pending SAP export"
            )


# ============================================================
# FUTURE SAP ATTACHMENT STAGE
# ============================================================

def attach_to_sap():
    """
    FUTURE FUNCTION

    This is intentionally not implemented yet.

    Once the company's approved SAP Business One attachment
    interface is confirmed, this function will:

        1. Receive the Kubo PDF path.
        2. Receive the SAP DocNum.
        3. Upload/create the SAP attachment.
        4. Link it to the SAP Delivery Note.
        5. Verify that the attachment was accepted.
        6. Return SUCCESS or FAILED.

    Until then, TO_ATTACH is only a decision.
    No SAP record is modified.
    """

    raise NotImplementedError(
        "SAP attachment integration has not been enabled yet."
    )


# ============================================================
# REPORT
# ============================================================

def write_report(results):

    fieldnames = [
        "Filename",
        "FilePath",
        "DeliveryNumber",
        "SAP_DocNum",
        "SAP_CardName",
        "SAP_DocDate",
        "Status",
        "Reason"
    ]

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(results)


# ============================================================
# SUMMARY
# ============================================================

def print_summary(results):

    to_attach = sum(
        1
        for row in results
        if row["Status"] == "TO_ATTACH"
    )

    skip = sum(
        1
        for row in results
        if row["Status"] == "SKIP"
    )

    review = sum(
        1
        for row in results
        if row["Status"] == "REVIEW"
    )

    print("\nPROCESSING COMPLETE")
    print("-" * 30)

    print(f"TO_ATTACH : {to_attach}")
    print(f"SKIP      : {skip}")
    print(f"REVIEW    : {review}")

    print("\nReport saved to:")
    print(OUTPUT_FILE)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 65)
    print("KUBO -> SAP ATTACHMENT AUTOMATION")
    print("=" * 65)

    # --------------------------------------------------------
    # KUBO
    # --------------------------------------------------------

    print("\nKUBO SOURCE")
    print("-" * 30)

    print(KUBO_FOLDER)

    log_message(f"Kubo folder resolved to: {KUBO_FOLDER}")

    print("\nScanning Kubo PDFs...")

    results = scan_kubo_folder()

    print(
        f"PDF files found: {len(results)}"
    )

    # --------------------------------------------------------
    # GEORGE / SAP
    # --------------------------------------------------------

    print("\nSAP SOURCE")
    print("-" * 30)

    pending_sap, source_used = get_pending_delivery_notes()

    print(f"Source used this run: {source_used}")
    print(
        f"Pending SAP delivery notes loaded: "
        f"{len(pending_sap)}"
    )

    # --------------------------------------------------------
    # MATCH
    # --------------------------------------------------------

    print(
        "\nMatching Kubo delivery numbers "
        "against SAP DocNum..."
    )

    match_kubo_to_sap(
        results,
        pending_sap
    )

    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    write_report(results)

    print_summary(results)

    # --------------------------------------------------------
    # SAP ATTACHMENT EXECUTION
    # --------------------------------------------------------

    if os.environ.get("KUBO_ATTACH", "0") == "1":
        print("\nStarting SAP attachment execution...")
        run_attachment_pipeline()
    else:
        print("\nREAD-ONLY run: attachment step skipped (set KUBO_ATTACH=1 to enable).")

    log_message(
        f"Run complete. Source={source_used}, "
        f"TO_ATTACH={sum(1 for r in results if r['Status'] == 'TO_ATTACH')}, "
        f"SKIP={sum(1 for r in results if r['Status'] == 'SKIP')}, "
        f"REVIEW={sum(1 for r in results if r['Status'] == 'REVIEW')}"
    )


# ============================================================
# PROGRAM ENTRY
# ============================================================

if __name__ == "__main__":
    main()

