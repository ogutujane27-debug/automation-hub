import requests

# Disable SSL warnings if using self-signed development certificates
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SAPServiceLayerClient:
    def __init__(self, base_url, company_db, username, password):
        self.base_url = base_url.rstrip('/')
        self.credentials = {
            "CompanyDB": company_db,
            "UserName": username,
            "Password": password
        }
        self.session = requests.Session()
        # Service Layer typically uses self-signed certificates in dev/sandbox environments
        self.session.verify = False 

    def login(self):
        """Authenticates against SAP Service Layer and stores the B1SESSION cookie."""
        login_url = f"{self.base_url}/Login"
        response = self.session.post(login_url, json=self.credentials)
        
        if response.status_code == 200:
            print("Successfully authenticated with SAP Service Layer.")
            return True
        else:
            print(f"SAP Login Failed [{response.status_code}]: {response.text}")
            return False

    def create_invoice(self, invoice_payload):
        """Pushes a structured invoice payload to SAP Invoices endpoint."""
        invoices_url = f"{self.base_url}/Invoices"
        response = self.session.post(invoices_url, json=invoice_payload)
        
        if response.status_code == 201:
            data = response.json()
            print(f"Successfully created SAP Invoice. DocEntry: {data.get('DocEntry')}")
            return data
        else:
            print(f"Failed to create invoice [{response.status_code}]: {response.text}")
            return None

    def logout(self):
        """Closes the active SAP session."""
        logout_url = f"{self.base_url}/Logout"
        self.session.post(logout_url)
        print("Logged out from SAP Service Layer.")