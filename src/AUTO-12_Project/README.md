# AUTO-12: Recurring Invoices

## What it does
Recurring monthly supplier invoices for IAL and AZL. Each recurring charge is set up once as a template. Invoices are generated from the templates, a person approves them, and approved invoices are posted to SAP as A/P invoices. Every action is recorded in an audit trail. It runs against the dev company (IAL01_DEV) only for now.

## Pipeline
1. Templates: each recurring charge is entered in the dashboard with its supplier, GL account, cost centre, amount (fixed or variable), category and schedule.
2. Generate: invoices for each due period are created as Pending. One invoice per template per period; a duplicate is blocked by the database.
3. Approve: an Admin approves a Pending invoice by re-entering their password. Pending or Failed invoices can be cancelled. An Admin can delete an invoice with their password, except once SAP has accepted it.
4. Post: the sync command posts Approved invoices to SAP as PurchaseInvoices. It runs as a dry run unless told to execute, and execute is limited to the dev companies.
5. Record: an append-only audit trail (who, what, when) and failure alert emails.

Roles: Viewer, Preparer, Admin. Login is by token, and login attempts are throttled.

## Settings
Names only. See .env.example. Environment variables override .env.
- SECRET_KEY, DEBUG: Django
- SAP_BASE_URL, SAP_COMPANY_DB, SAP_USER, SAP_PASSWORD, SAP_INVOICE_SERIES: SAP Service Layer
- HANA_HOST, HANA_PORT and the HANA login: SAP HANA
- MAIL_*, SMTP_*, ALERT_EMAIL_TO: email and failure alerts

Safety: nothing is written to SAP unless the sync is run with execute, and execute refuses non-dev companies.

## How to run
- Backend: Django app (recurring_invoices) with a REST API.
- Dashboard: React/Vite app in frontend\.
- run_app.bat starts the app. run_full_sync.ps1 runs the SAP sync.

## Status
- Built and tested in the dev company only.
- Done: login and roles, audit trail, approvals, duplicate block, dry-run sync.
- Open: the first successful post to SAP (the first test post failed with a SAP lookup error and nothing was created), live company names for IAL and AZL, and a server to run it on.

## Docs
Full documentation: docs\ (to be added)
