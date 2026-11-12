Write-Host "--- Step 1: Running SAP Invoice Sync ---" -ForegroundColor Cyan
python manage.py sync_sap_invoices

Write-Host "`n--- Step 2: Emailing alerts for failed invoices ---" -ForegroundColor Cyan
python manage.py send_failure_alerts

Write-Host "`n--- Step 3: Verifying Created Invoices ---" -ForegroundColor Cyan
python check_today.py

Write-Host "`nAutomation workflow completed." -ForegroundColor Green