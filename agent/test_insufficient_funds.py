import json
import os
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv(Path(__file__).parent / ".env")
BASE_URL = os.getenv("DEMOBANK_URL", "http://localhost:5173").rstrip("/")
API_URL = "http://localhost:8000"

CHECKING_ID = "00000000-0000-0000-0000-000000000101"
SAVINGS_ID = "00000000-0000-0000-0000-000000000102"

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    try:
        page.goto(BASE_URL)
        page.get_by_role("button", name="Enter Demo").click()

        before_response = context.request.get(f"{API_URL}/api/accounts")
        assert before_response.ok, f"Cannot read accounts: {before_response.status}"
        before_data = before_response.json()
        print("BEFORE:", json.dumps(before_data, indent=2))

        accounts = before_data["accounts"]
        balances = {a["id"]: Decimal(str(a["balance"])) for a in accounts}

        source_balance = balances[CHECKING_ID]
        amount = source_balance + Decimal("100.00")

        print(f"\nAttempting transfer of ${amount} from checking to savings")
        print("Expected: HTTP 409 and no balance changes")

        response = context.request.post(
            f"{API_URL}/api/transfers",
            data={
                "source_account_id": CHECKING_ID,
                "destination_account_id": SAVINGS_ID,
                "amount": str(amount),
                "memo": "QA insufficient funds test",
            },
        )

        print("\nTRANSFER STATUS:", response.status)
        print("TRANSFER BODY:", response.text())

        after_response = context.request.get(f"{API_URL}/api/accounts")
        assert after_response.ok, f"Cannot read accounts afterward: {after_response.status}"
        after_data = after_response.json()
        after_balances = {
            a["id"]: Decimal(str(a["balance"]))
            for a in after_data["accounts"]
        }

        print("\nBEFORE BALANCES:", balances)
        print("AFTER BALANCES:", after_balances)

        if response.status == 409 and balances == after_balances:
            print("\nTC-022: PASS")
        else:
            print("\nTC-022: FAIL - Potential DB-QA-002")
            print("Inspect the response and balances before drawing a conclusion.")

        Path("tc022_result.json").write_text(
            json.dumps(
                {
                    "test_id": "TC-022",
                    "response_status": response.status,
                    "response_body": response.text(),
                    "balances_before": {k: str(v) for k, v in balances.items()},
                    "balances_after": {k: str(v) for k, v in after_balances.items()},
                },
                indent=2,
            )
        )
    finally:
        browser.close()
