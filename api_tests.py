import pandas as pd
import requests

BASE_URL = "http://localhost:8000"  # Update with your server URL


def test_login_api(data):
    url = f"{BASE_URL}/api/login/"
    for _, row in data.iterrows():
        payload = {
            "customer_id": row["customer_id"],
            "password": row["password"],
            "pan": row["pan"]
        }
        response = requests.post(url, json=payload)
        print(f"Login API | {payload} | {response.status_code} | {response.json()}")


def test_create_customer(data):
    url = f"{BASE_URL}/api/customers/"
    for _, row in data.iterrows():
        payload = {
            "full_name": row["full_name"],
            "dob": row["dob"],
            "email": row["email"],
            "phone_number": row["phone_number"],
            "customer_id": row["customer_id"],
            "password": row["password"],
            "aadhar_number": row["aadhar_number"],
            "pan": row["pan"],
            "communication_address": row["communication_address"],
            "permanent_address": row["permanent_address"],
        }
        files = {
            "aadhar_document": open(row["aadhar_document"], "rb"),
            "pan_document": open(row["pan_document"], "rb"),
        }
        response = requests.post(url, data=payload, files=files)
        print(f"Create Customer | {payload} | {response.status_code} | {response.json()}")


def test_create_account(data):
    url = f"{BASE_URL}/api/accounts/"
    for _, row in data.iterrows():
        payload = {
            "customer": row["customer_id"],
            "account_number": row["account_number"],
            "ifsc_code": row["ifsc_code"],
            "account_type": row["account_type"],
            "kyc_status": row["kyc_status"],
        }
        response = requests.post(url, json=payload)
        print(f"Create Account | {payload} | {response.status_code} | {response.json()}")


def test_cash_deposit(data):
    url = f"{BASE_URL}/api/cash-deposits/"
    for _, row in data.iterrows():
        payload = {
            "account": row["account_id"],
            "amount": row["amount"],
        }
        response = requests.post(url, json=payload)
        print(f"Cash Deposit | {payload} | {response.status_code} | {response.json()}")


def test_interbank_transfer(data):
    url = f"{BASE_URL}/api/interbank-transfers/"
    for _, row in data.iterrows():
        payload = {
            "sender_account": row["sender_account_id"],
            "receiver_account": row["receiver_account_id"],
            "amount": row["amount"],
            "transfer_method": row["transfer_method"],
        }
        response = requests.post(url, json=payload)
        print(f"InterBank Transfer | {payload} | {response.status_code} | {response.json()}")


def test_other_bank_transfer(data):
    url = f"{BASE_URL}/api/otherbank-transfers/"
    for _, row in data.iterrows():
        payload = {
            "sender_account": row["sender_account_id"],
            "receiver_name": row["receiver_name"],
            "receiver_account_number": row["receiver_account_number"],
            "receiver_ifsc_code": row["receiver_ifsc_code"],
            "amount": row["amount"],
            "transfer_method": row["transfer_method"],
        }
        response = requests.post(url, json=payload)
        print(f"Other Bank Transfer | {payload} | {response.status_code} | {response.json()}")


if __name__ == "__main__":
    # Load Excel data
    excel_file = "test_data_template.xlsx"
    login_data = pd.read_excel(excel_file, sheet_name="LoginAPI")
    customer_data = pd.read_excel(excel_file, sheet_name="CustomerAPI")
    account_data = pd.read_excel(excel_file, sheet_name="AccountAPI")
    cash_deposit_data = pd.read_excel(excel_file, sheet_name="CashDepositAPI")
    interbank_data = pd.read_excel(excel_file, sheet_name="InterBankTransferAPI")
    other_bank_data = pd.read_excel(excel_file, sheet_name="OtherBankTransferAPI")

    # Run Tests
    test_login_api(login_data)
    test_create_customer(customer_data)
    test_create_account(account_data)
    test_cash_deposit(cash_deposit_data)
    test_interbank_transfer(interbank_data)
    test_other_bank_transfer(other_bank_data)
