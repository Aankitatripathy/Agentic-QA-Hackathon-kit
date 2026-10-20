from decimal import Decimal
from pathlib import Path
import json

from playwright.sync_api import expect

CHECKING_ID = "00000000-0000-0000-0000-000000000101"
SAVINGS_ID = "00000000-0000-0000-0000-000000000102"
API_URL = "http://localhost:8000"


def read_balances(page):
    response = page.context.request.get(f"{API_URL}/api/accounts")
    if response.status != 200:
        raise RuntimeError(
            f"Cannot read accounts: HTTP {response.status}: {response.text()}"
        )

    return {
        account["id"]: Decimal(str(account["balance"]))
        for account in response.json()["accounts"]
    }


def open_transfer(page):
    page.goto(page.url.split("/")[0] + "//" +
              page.url.split("/")[2] + "/transfer")
    expect(
        page.get_by_role(
            "heading",
            name="Transfer between your accounts",
        )
    ).to_be_visible(timeout=10000)
    expect(page.locator("#source")).to_be_visible()
    expect(page.locator("#destination")).to_be_visible()


def run_transfer_validation_tests(page, results, update_result, save_evidence):
    def record(test_id, passed, details):
        screenshot = save_evidence(
            page, f"{test_id}_transfer_validation.png"
        )
        update_result(
            results,
            test_id,
            "PASS" if passed else "FAIL",
            details,
            screenshot,
        )
        print(f"{test_id}: {'PASS' if passed else 'FAIL'}")

    def check_rejected(test_id, amount, same_account=False):
        open_transfer(page)

        page.locator("#source").select_option(CHECKING_ID)
        page.locator("#destination").select_option(
            CHECKING_ID if same_account else SAVINGS_ID
        )
        page.locator("#amount").fill(amount)

        before = read_balances(page)

        with page.expect_response(
            lambda response:
                response.request.method == "POST"
                and response.url.endswith("/api/transfers"),
            timeout=10000,
        ) as response_info:
            page.get_by_role(
                "button", name="Transfer funds"
            ).click()

        response = response_info.value
        after = read_balances(page)

        rejected = response.status in (400, 409, 422)
        unchanged = before == after
        no_success = (
            page.get_by_text("Transfer complete", exact=True).count() == 0
        )

        passed = rejected and unchanged and no_success
        details = (
            f"Amount={amount!r}; HTTP {response.status}; "
            f"balances unchanged={unchanged}; "
            f"no success message={no_success}; "
            f"response={response.text()[:300]}"
        )
        record(test_id, passed, details)

    # TC-015: Form structure and optional memo.
    open_transfer(page)
    fields_present = all(
        page.locator(selector).is_visible()
        for selector in ("#source", "#destination", "#amount", "#memo")
    )
    memo_optional = "optional" in (
        page.locator('label[for="memo"]').inner_text().lower()
    )
    record(
        "TC-015",
        fields_present and memo_optional,
        "Source, destination, amount, and optional memo verified.",
    )

    # TC-016: Same-account transfer.
    check_rejected("TC-016", "10.00", same_account=True)

    # TC-017: Blank amount is rejected by frontend.
    open_transfer(page)
    page.locator("#amount").fill("")
    before = read_balances(page)
    page.get_by_role("button", name="Transfer funds").click()
    expect(page.locator("#amount-error")).to_be_visible()
    after = read_balances(page)
    record(
        "TC-017",
        before == after,
        "Blank amount rejected with field error; balances unchanged.",
    )

    # TC-018 and TC-019 are confirmed defects.
    # Import their saved evidence instead of repeating unsafe transfers.
    previous_report = Path(__file__).resolve().parent / "qa_report.json"

    if previous_report.exists():
        saved = json.loads(previous_report.read_text(encoding="utf-8"))
        for test_id in ("TC-018", "TC-019"):
            previous = next(
                (r for r in saved.get("results", [])
                 if r.get("test_id") == test_id),
                None,
            )
            if previous and previous.get("status") == "FAIL":
                update_result(
                    results,
                    test_id,
                    "FAIL",
                    previous["details"],
                    previous.get("screenshot"),
                )
                print(f"{test_id}: FAIL (saved evidence)")
            else:
                print(f"{test_id}: UNVERIFIED (saved evidence unavailable)")

    # These invalid inputs have been verified as safely rejected.
    for test_id, amount in [
        ("TC-020", "abc"),
        ("TC-021", "10.123"),
    ]:
        check_rejected(test_id, amount)
