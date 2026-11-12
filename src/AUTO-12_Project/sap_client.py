import os
import requests
import urllib3
from dotenv import load_dotenv

# Self-signed certificates on the dev/sandbox Service Layer
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()


class SAPServiceLayerClient:
    def __init__(self, company_db=None):
        self.base_url = os.getenv("SAP_BASE_URL", "").rstrip('/')
        self.company_db = company_db or os.getenv("SAP_COMPANY_DB")
        self.credentials = {
            "CompanyDB": self.company_db,
            "UserName": os.getenv("SAP_USER"),
            "Password": os.getenv("SAP_PASSWORD"),
        }
        self.session = requests.Session()
        self.session.verify = False

    def login(self):
        """Authenticates against the SAP Service Layer and establishes a session cookie."""
        try:
            response = self.session.post(f"{self.base_url}/Login", json=self.credentials, timeout=15)
            if response.status_code == 200:
                print(f"[SAP] Successfully authenticated ({self.company_db}).")
                return True
            print(f"[SAP] Login failed [{response.status_code}]: {response.text}")
            return False
        except requests.exceptions.RequestException as e:
            print(f"[SAP] Connection error during login: {e}")
            return False

    def get(self, path):
        return self.session.get(f"{self.base_url}/{path}", timeout=20)

    def exists(self, path):
        try:
            return self.get(path).status_code == 200
        except requests.exceptions.RequestException:
            return False

    def create_purchase_invoice(self, payload):
        """Posts an A/P (purchase) invoice. Returns (data, error_text); exactly one is None."""
        try:
            r = self.session.post(f"{self.base_url}/PurchaseInvoices", json=payload, timeout=30)
        except requests.exceptions.RequestException as e:
            return None, f"Connection error: {e}"
        if r.status_code == 201:
            return r.json(), None
        try:
            msg = r.json().get('error', {}).get('message', {}).get('value') or r.text
        except ValueError:
            msg = r.text
        return None, f"[{r.status_code}] {msg}"

    def logout(self):
        """Closes the active SAP Service Layer session."""
        try:
            self.session.post(f"{self.base_url}/Logout", timeout=10)
            print("[SAP] Successfully logged out.")
        except requests.exceptions.RequestException:
            print("[SAP] Warning: Logout request timed out or failed.")
