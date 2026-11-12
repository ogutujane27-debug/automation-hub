import os
import win32com.client


print("=" * 70)
print("SAP BUSINESS ONE DI API — CONNECTION TEST")
print("=" * 70)

company = win32com.client.Dispatch("SAPbobsCOM.Company")

company.Server = os.environ.get("HANA_HOST", "")
company.DbServerType = 15
company.DbUserName = os.environ.get("HANA_USER", "")
company.DbPassword = os.environ.get("HANA_PASSWORD", "")
company.CompanyDB = os.environ.get("HANA_DATABASE", "")
company.UserName = os.environ.get("HANA_USER", "")
company.Password = os.environ.get("HANA_PASSWORD", "")

print()
print("CONNECTION DETAILS")
print("-" * 30)
print("Server     :", company.Server)
print("Database   :", company.CompanyDB)
print("DB User    :", company.DbUserName)
print("SAP User   :", company.UserName)
print("Password   : [hidden]")
print()

print("Attempting DI API connection...")

result = company.Connect()

print()
print("Connect() result:", result)

if result == 0:
    print()
    print("SUCCESS — SAP BUSINESS ONE DI API CONNECTED")
    print("Company:", company.CompanyName)
    print("Database:", company.CompanyDB)
    print("Version:", company.Version)
else:
    print()
    print("CONNECTION FAILED")
    print("Error code:", company.GetLastErrorCode())
    print("Error message:", company.GetLastErrorDescription())

if company.Connected:
    company.Disconnect()
    print()
    print("Disconnected cleanly.")