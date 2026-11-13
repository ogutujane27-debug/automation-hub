# Kubo Attachment Automation

## What it does
Kubo's signed delivery proofs arrive as PDFs in a shared folder. Each delivery note in SAP Business One needs a link to its PDF in the field U_Attachment. This job matches each PDF to its delivery note and writes the link into SAP, so nobody has to do it by hand. It is built and tested in the dev company (IAL01_DEV). Going live on the real company is a separate decision.

## Pipeline
1. Input: scan Kubo's PDF folder for one month (set by KUBO_MONTH_OVERRIDE).
2. Match: the first 8 digits of the file name are the delivery number. It is looked up in SAP HANA (table ODLN) among delivery notes that have no link yet. A name without a safe 8-digit number is never guessed.
3. Attach: the link is written through the SAP Service Layer, then read back to verify. The identical PDF must already be in the SAP attachments share. Nothing is copied, moved or deleted.
4. Result for each PDF:
   - TO_ATTACH: in SAP's pending list, so the job tries to attach it
   - ATTACHED: written and verified
   - SKIP: already linked, or not in this company
   - REVIEW: no safe delivery number, or SAP refused the write. A person looks at it.
5. Report: a CSV decision report, one summary line per run, and emails on attach, on error, and a daily digest of deliveries SAP refused.

Rules that never change: an existing link is never overwritten, nothing in either file share is copied, moved or deleted, and the first 8 digits decide the match.

## Settings
Names only. See .env.example. Environment variables override .env.
- SL_*, HANA_*, DATA_SOURCE: connections to SAP
- KUBO_ATTACH: safety switch. 0 = read-only (scan and report), 1 = attach.
- KUBO_ONLY_DOCNUM: limits a run to one delivery or a list
- KUBO_MONTH_OVERRIDE, KUBO_BASE_FOLDER: which Kubo folder to scan
- SAP_ATTACHMENT_FOLDER, KUBO_LINK_PREFIX, KUBO_NO_COPY, KUBO_LINK_ONLY: where links point
- KUBO_REFUSAL_RETRY_HOURS: how long a refused delivery is not asked again
- SMTP_*, MAIL_TO: email

## How to run
- python run_kubo.py is the wrapper: it takes a lock file, runs the job, writes the summary line and sends the emails.
- app\Kubo_Attachment_Automation.py is the worker that scans and matches.
- one.bat and all.bat run one delivery or everything pending.
- Schedule: every 2 hours.

## Status
- Runs today from a separate working copy on the laptop. Moving it into this hub folder is in progress.
- Tested in dev: 4,200 PDFs gave 11 TO_ATTACH, 4,154 SKIP and 35 REVIEW.
- The 11 TO_ATTACH are refused by SAP rule SD017 (invalid truck number). They stay REVIEW and are not retried for 24 hours.
- Open: a Linux server, and the conditions for going live.

## Docs
Full documentation: docs\
