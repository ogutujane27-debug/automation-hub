from sap_client import SAPServiceLayerClient

client = SAPServiceLayerClient()
if client.login():
    try:
        # Use raw string or standard URL concatenation to avoid escaping issues
        url = f"{client.base_url}/BusinessPartners?$select=CardCode,CardName&$top=50"
        response = client.session.get(url, verify=False)
        if response.status_code == 200:
            data = response.json().get('value', [])
            print("--- Available SAP Business Partners ---")
            for bp in data:
                print(f"CardCode: {bp.get('CardCode')} | Name: {bp.get('CardName')}")
        else:
            print(f"Failed to fetch Business Partners: {response.status_code} - {response.text}")
    finally:
        client.logout()
else:
    print("SAP Login failed.")
