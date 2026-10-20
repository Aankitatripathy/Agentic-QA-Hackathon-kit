
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from transfer_validation_tests import run_transfer_validation_tests
from dashboard_session_tests import run_dashboard_session_tests
from remaining_ui_tests import run_remaining_ui_tests
from transfer_feedback_tests import run_transfer_feedback_tests
from successful_transfer_tests import run_successful_transfer_tests


# ============================================================
# CONFIGURATION
# ============================================================

BASE = Path(__file__).resolve().parent
EVIDENCE = BASE / "evidence"
EVIDENCE.mkdir(parents=True, exist_ok=True)

load_dotenv(BASE / ".env")

TARGET_URL = os.getenv("DEMOBANK_URL", "").strip().rstrip("/")

CHECKING_ID = "00000000-0000-0000-0000-000000000101"
ANNUAL_BONUS_ID = "00000000-0000-0000-0000-000000000208"


# ============================================================
# REPORT HELPERS
# ============================================================

def make_result(test_id, requirement_id):
    return {
        "test_id": test_id,
        "requirement_id": requirement_id,
        "status": "UNVERIFIED",
        "details": "Test has not been executed.",
        "screenshot": None,
    }


def update_result(
    results,
    test_id,
    status,
    details,
    screenshot=None,
):
    for result in results:
        if result["test_id"] == test_id:
            result["status"] = status
            result["details"] = details
            result["screenshot"] = screenshot
            return

    raise ValueError(f"Test case not found: {test_id}")


def save_evidence(page, filename):
    path = EVIDENCE / filename

    page.screenshot(
        path=str(path),
        full_page=True,
    )

    return str(path)


def record_test_result(
    page,
    results,
    test_id,
    passed,
    success_message,
    errors,
    screenshot_name,
):
    screenshot = save_evidence(page, screenshot_name)

    status = "PASS" if passed else "FAIL"

    details = (
        success_message
        if passed
        else "; ".join(errors)
    )

    update_result(
        results,
        test_id,
        status,
        details,
        screenshot,
    )

    print(f"{test_id}: {status}")
    print(f"Evidence: {screenshot}")


# ============================================================
# PAGE HELPERS
# ============================================================

def open_transactions(page):
    page.goto(
        f"{TARGET_URL}/transactions",
        wait_until="domcontentloaded",
        timeout=15000,
    )

    page.get_by_role(
        "heading",
        name="Transactions",
        exact=True,
    ).wait_for(
        state="visible",
        timeout=15000,
    )

    page.get_by_test_id("result-count").or_(
        page.get_by_text("No transactions yet")
    ).or_(
        page.get_by_text("We couldn't load transactions")
    ).first.wait_for(
        state="visible",
        timeout=15000,
    )


def wait_for_transaction_response(page, click_action):
    with page.expect_response(
        lambda response: (
            "/api/transactions" in response.url
            and response.request.method == "GET"
        ),
        timeout=15000,
    ) as response_info:
        click_action()

    response = response_info.value

    if response.status != 200:
        raise RuntimeError(
            f"Transactions API returned HTTP {response.status}"
        )

    return response


def apply_date_filters(page, start_date, end_date):
    page.locator("#filter-start").fill(start_date)
    page.locator("#filter-end").fill(end_date)

    wait_for_transaction_response(
        page,
        lambda: page.get_by_role(
            "button",
            name="Apply filters",
            exact=True,
        ).click(),
    )

    page.get_by_role(
        "heading",
        name="Filtered results",
        exact=True,
    ).wait_for(
        state="visible",
        timeout=15000,
    )

    page.get_by_text(
        "Annual bonus",
        exact=True,
    ).or_(
        page.get_by_text(
            "No transactions match these filters",
            exact=True,
        )
    ).first.wait_for(
        state="visible",
        timeout=15000,
    )


def bonus_is_visible(page):
    bonus = page.get_by_text(
        "Annual bonus",
        exact=True,
    )

    return (
        bonus.count() > 0
        and bonus.first.is_visible()
    )


# ============================================================
# TC-029: TRANSACTION DETAILS
# ============================================================

def test_transaction_details(page, results):
    print("\nRunning TC-029: Transaction row details")

    open_transactions(page)

    table = page.get_by_test_id("transaction-table")
    rows = page.get_by_test_id("transaction-row")

    expected_headers = [
        "Date & time",
        "Description",
        "Type",
        "Account",
        "Amount",
        "Status",
    ]

    # FIX: Compare headers without case sensitivity.
    # CSS may display labels in uppercase.
    actual_headers = [
        value.strip().lower()
        for value in table.locator(
            "thead th"
        ).all_inner_texts()
    ]

    expected_headers = [
        header.lower()
        for header in expected_headers
    ]

    errors = []

    if actual_headers != expected_headers:
        errors.append(
            f"Incorrect table headers: {actual_headers}"
        )

    row_count = rows.count()

    if row_count != 12:
        errors.append(
            f"Expected 12 seeded transactions; found {row_count}"
        )

    for row in rows.all():
        cells = row.locator("td")

        if cells.count() != 6:
            errors.append(
                "Transaction row does not contain six cells."
            )
            continue

        transaction_id = row.get_attribute(
            "data-transaction-id"
        )

        if not transaction_id:
            errors.append(
                "Transaction ID is missing."
            )

        timestamp = cells.nth(0).locator(
            "time[datetime]"
        )

        if timestamp.count() == 0:
            errors.append(
                "Transaction timestamp is missing."
            )

        for index in range(1, 6):
            cell_text = cells.nth(index).inner_text().strip()

            if not cell_text:
                errors.append(
                    f"Empty transaction column {index + 1}."
                )

    expected_transactions = {
        "Demo payroll": (
            "Deposit",
            "Completed",
            "credit",
        ),
        "Demo groceries": (
            "Withdrawal",
            "Completed",
            "debit",
        ),
        "Annual bonus": (
            "Deposit",
            "Completed",
            "credit",
        ),
    }

    for description, expected in expected_transactions.items():
        expected_type, expected_status, direction = expected

        matching_rows = rows.filter(
            has_text=description
        )

        if matching_rows.count() != 1:
            errors.append(
                f"Expected exactly one row for {description}."
            )
            continue

        row = matching_rows.first
        cells = row.locator("td")

        actual_type = cells.nth(2).inner_text().strip()
        actual_status = cells.nth(5).inner_text().strip()

        if actual_type != expected_type:
            errors.append(
                f"Incorrect type for {description}."
            )

        if actual_status != expected_status:
            errors.append(
                f"Incorrect status for {description}."
            )

        amount_class = (
            cells.nth(4).get_attribute("class") or ""
        )

        if f"amount--{direction}" not in amount_class:
            errors.append(
                f"Incorrect amount direction for {description}."
            )

    record_test_result(
        page=page,
        results=results,
        test_id="TC-029",
        passed=len(errors) == 0,
        success_message=(
            "Verified six columns, 12 seeded transactions, "
            "transaction IDs, timestamps, required details, "
            "and positive/negative amount directions."
        ),
        errors=errors,
        screenshot_name="TC-029_transaction_details.png",
    )


# ============================================================
# TC-030: COMBINED FILTERS
# ============================================================

def test_combined_filters(page, results):
    print("\nRunning TC-030: Combined transaction filters")

    open_transactions(page)

    page.locator(
        "#filter-account"
    ).select_option(CHECKING_ID)

    page.locator(
        "#filter-type"
    ).select_option("deposit")

    page.locator(
        "#filter-status"
    ).select_option("completed")

    page.locator(
        "#filter-start"
    ).fill("2025-06-15")

    page.locator(
        "#filter-end"
    ).fill("2025-06-17")

    wait_for_transaction_response(
        page,
        lambda: page.get_by_role(
            "button",
            name="Apply filters",
            exact=True,
        ).click(),
    )

    page.get_by_test_id(
        "result-count"
    ).wait_for(
        state="visible",
        timeout=15000,
    )

    rows = page.get_by_test_id("transaction-row")

    errors = []

    if rows.count() != 1:
        errors.append(
            f"Expected 1 matching transaction; found {rows.count()}."
        )

    else:
        row = rows.first
        cells = row.locator("td")

        transaction_id = row.get_attribute(
            "data-transaction-id"
        )

        description = cells.nth(1).inner_text()
        tx_type = cells.nth(2).inner_text().strip()
        account = cells.nth(3).inner_text()
        status = cells.nth(5).inner_text().strip()

        if transaction_id != ANNUAL_BONUS_ID:
            errors.append(
                "Unexpected transaction ID."
            )

        if "Annual bonus" not in description:
            errors.append(
                "Expected Annual bonus transaction."
            )

        if tx_type != "Deposit":
            errors.append(
                "Transaction type should be Deposit."
            )

        if "1042" not in account:
            errors.append(
                "Transaction should belong to Checking."
            )

        if status != "Completed":
            errors.append(
                "Transaction status should be Completed."
            )

    record_test_result(
        page=page,
        results=results,
        test_id="TC-030",
        passed=len(errors) == 0,
        success_message=(
            "Combined Checking account, Deposit type, "
            "Completed status, and June 15-17, 2025 "
            "date range. Only Annual bonus appeared."
        ),
        errors=errors,
        screenshot_name="TC-030_combined_filters.png",
    )


# ============================================================
# TC-031: INCLUSIVE END DATE
# ============================================================

def test_end_date_filter(page, results):
    print("\nRunning TC-031: Inclusive end-date filter")

    open_transactions(page)

    apply_date_filters(
        page,
        "2025-06-15",
        "2025-06-15",
    )

    passed = bonus_is_visible(page)

    errors = []

    if not passed:
        errors.append(
            "BUG DB-QA-001: Annual bonus (+$950.00) "
            "occurred on June 15, 2025, but was excluded "
            "when the start and end dates were both "
            "June 15, 2025. The PRD requires inclusive "
            "date boundaries in Pacific Time."
        )

    record_test_result(
        page=page,
        results=results,
        test_id="TC-031",
        passed=passed,
        success_message=(
            "Annual bonus appeared on the selected end date."
        ),
        errors=errors,
        screenshot_name="TC-031_end_date.png",
    )


# ============================================================
# TC-032: INCLUSIVE START DATE
# ============================================================

def test_start_date_filter(page, results):
    print("\nRunning TC-032: Inclusive start-date filter")

    open_transactions(page)

    apply_date_filters(
        page,
        "2025-06-15",
        "2025-06-17",
    )

    passed = bonus_is_visible(page)

    errors = []

    if not passed:
        errors.append(
            "Annual bonus (+$950.00) was missing "
            "from the selected start-date boundary."
        )

    record_test_result(
        page=page,
        results=results,
        test_id="TC-032",
        passed=passed,
        success_message=(
            "Annual bonus was correctly included "
            "on the selected start date."
        ),
        errors=errors,
        screenshot_name="TC-032_start_date.png",
    )


# ============================================================
# TC-033: EMPTY STATE
# ============================================================

def test_empty_state(page, results):
    print("\nRunning TC-033: No matching transactions")

    open_transactions(page)

    page.locator(
        "#filter-start"
    ).fill("2035-01-01")

    page.locator(
        "#filter-end"
    ).fill("2035-01-31")

    wait_for_transaction_response(
        page,
        lambda: page.get_by_role(
            "button",
            name="Apply filters",
            exact=True,
        ).click(),
    )

    empty_state = page.get_by_text(
        "No transactions match these filters",
        exact=True,
    )

    empty_state.wait_for(
        state="visible",
        timeout=15000,
    )

    no_rows = (
        page.get_by_test_id(
            "transaction-row"
        ).count() == 0
    )

    passed = empty_state.is_visible() and no_rows

    errors = []

    if not passed:
        errors.append(
            "Expected an empty state with no transaction rows."
        )

    record_test_result(
        page=page,
        results=results,
        test_id="TC-033",
        passed=passed,
        success_message=(
            "Filtering to January 2035 displayed "
            "the expected empty-state message "
            "with no transaction rows."
        ),
        errors=errors,
        screenshot_name="TC-033_empty_state.png",
    )


# ============================================================
# TC-034: CLEAR FILTERS
# ============================================================

def test_clear_filters(page, results):
    print("\nRunning TC-034: Clear filters restores history")

    open_transactions(page)

    initial_count = page.get_by_test_id(
        "result-count"
    ).inner_text().strip()

    page.locator(
        "#filter-start"
    ).fill("2035-01-01")

    page.locator(
        "#filter-end"
    ).fill("2035-01-31")

    wait_for_transaction_response(
        page,
        lambda: page.get_by_role(
            "button",
            name="Apply filters",
            exact=True,
        ).click(),
    )

    page.get_by_text(
        "No transactions match these filters",
        exact=True,
    ).wait_for(
        state="visible",
        timeout=15000,
    )

    filter_form = page.get_by_role(
        "form",
        name="Filter transactions",
    )

    wait_for_transaction_response(
        page,
        lambda: filter_form.get_by_role(
            "button",
            name="Clear filters",
            exact=True,
        ).click(),
    )

    page.get_by_test_id(
        "result-count"
    ).get_by_text(
        initial_count,
        exact=True,
    ).wait_for(
        state="visible",
        timeout=15000,
    )

    restored_count = page.get_by_test_id(
        "result-count"
    ).inner_text().strip()

    start_cleared = (
        page.locator(
            "#filter-start"
        ).input_value() == ""
    )

    end_cleared = (
        page.locator(
            "#filter-end"
        ).input_value() == ""
    )

    all_transactions_visible = page.get_by_role(
        "heading",
        name="All transactions",
        exact=True,
    ).is_visible()

    errors = []

    if restored_count != initial_count:
        errors.append(
            "Original transaction count was not restored."
        )

    if not start_cleared:
        errors.append(
            "Start-date filter was not cleared."
        )

    if not end_cleared:
        errors.append(
            "End-date filter was not cleared."
        )

    if not all_transactions_visible:
        errors.append(
            "All transactions heading was not restored."
        )

    record_test_result(
        page=page,
        results=results,
        test_id="TC-034",
        passed=len(errors) == 0,
        success_message=(
            f"Original count: {initial_count}. "
            f"Restored count: {restored_count}. "
            "Date filters cleared and full history restored."
        ),
        errors=errors,
        screenshot_name="TC-034_clear_filters.png",
    )


# ============================================================
# MAIN QA EXECUTION
# ============================================================

def run():
    plan_path = BASE / "test_plan.json"

    plan = json.loads(
        plan_path.read_text(encoding="utf-8")
    )

    results = [
        make_result(
            test["test_id"],
            test["requirement_id"],
        )
        for test in plan["tests"]
    ]

    if not TARGET_URL:
        print(
            "ERROR: DEMOBANK_URL is missing from agent/.env"
        )

    else:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True
            )

            context = browser.new_context(
                viewport={
                    "width": 1280,
                    "height": 800,
                }
            )

            page = context.new_page()

            try:
                print(
                    f"Opening DemoBank: {TARGET_URL}"
                )

                response = page.goto(
                    TARGET_URL,
                    wait_until="domcontentloaded",
                    timeout=15000,
                )

                if response is None or response.status >= 400:
                    raise RuntimeError(
                        "DemoBank landing page failed to load."
                    )

                landing_screenshot = save_evidence(
                    page,
                    "landing_page.png",
                )

                print("Landing page loaded.")
                print(
                    f"Landing screenshot: {landing_screenshot}"
                )

                enter_demo = page.get_by_role(
                    "button",
                    name="Enter Demo",
                    exact=True,
                )

                if enter_demo.count() == 0:
                    enter_demo = page.get_by_role(
                        "link",
                        name="Enter Demo",
                        exact=True,
                    )

                if enter_demo.count() == 0:
                    raise RuntimeError(
                        "Enter Demo control was not found."
                    )

                enter_demo.first.click()

                page.wait_for_url(
                    "**/dashboard",
                    timeout=15000,
                )

                print("Demo session created.")
                print("Dashboard opened successfully.")

                tests = [
                    ("TC-029", test_transaction_details),
                    ("TC-030", test_combined_filters),
                    ("TC-031", test_end_date_filter),
                    ("TC-032", test_start_date_filter),
                    ("TC-033", test_empty_state),
                    ("TC-034", test_clear_filters),
                ]

                for test_id, test_function in tests:
                    try:
                        test_function(
                            page,
                            results,
                        )

                    except Exception as error:
                        print(
                            f"\n{test_id} execution error: {error}"
                        )

                        error_screenshot = None

                        try:
                            error_screenshot = save_evidence(
                                page,
                                f"{test_id}_error.png",
                            )
                        except Exception:
                            pass

                        update_result(
                            results,
                            test_id,
                            "UNVERIFIED",
                            (
                                "Test execution interrupted: "
                                f"{type(error).__name__}: {error}"
                            ),
                            error_screenshot,
                        )


                try:
                    print("\nRunning TC-015 through TC-021: Transfer validation")
                    run_transfer_validation_tests(
                        page,
                        results,
                        update_result,
                        save_evidence,
                    )
                except Exception as error:
                    print(f"Transfer validation execution error: {error}")
                    print("Any unfinished transfer tests remain UNVERIFIED.")

            except Exception as error:
                print(
                    f"\nBrowser setup error: {error}"
                )
                print(
                    "Unexecuted tests remain UNVERIFIED."
                )

            finally:
                context.close()
                browser.close()



    # Dashboard and session tests use their own isolated browser context.
    try:
        print("\nRunning TC-002 through TC-013: Dashboard and session tests")
        with sync_playwright() as dashboard_playwright:
            dashboard_browser = dashboard_playwright.chromium.launch(
                headless=True
            )
            try:
                run_dashboard_session_tests(
                    dashboard_browser,
                    TARGET_URL,
                    results,
                    update_result,
                    save_evidence,
                )
            finally:
                dashboard_browser.close()
    except Exception as error:
        print(f"Dashboard/session execution error: {error}")
        print("Unfinished dashboard/session tests remain UNVERIFIED.")


    try:
        print("\nRunning remaining read-only UI tests")
        with sync_playwright() as ui_playwright:
            ui_browser = ui_playwright.chromium.launch(headless=True)
            try:
                run_remaining_ui_tests(
                    ui_browser,
                    TARGET_URL,
                    results,
                    update_result,
                    save_evidence,
                )
            finally:
                ui_browser.close()
    except Exception as error:
        print(f"Read-only UI test execution error: {error}")


    try:
        print("\nRunning TC-026 and TC-040: Transfer feedback")
        with sync_playwright() as feedback_playwright:
            feedback_browser = feedback_playwright.chromium.launch(
                headless=True
            )
            try:
                run_transfer_feedback_tests(
                    feedback_browser,
                    TARGET_URL,
                    results,
                    update_result,
                    save_evidence,
                )
            finally:
                feedback_browser.close()
    except Exception as error:
        print(f"Transfer feedback test execution error: {error}")


    # Final successful-transfer tests are opt-in because they
    # change account balances and create ledger records.
    import os

    final_ids = {
        "TC-014", "TC-023", "TC-024",
        "TC-025", "TC-027",
    }

    if os.environ.get("QA_RUN_FINAL_TRANSFER") == "1":
        print("\nRunning final controlled $1 transfer")
        with sync_playwright() as final_playwright:
            final_browser = final_playwright.chromium.launch(
                headless=True
            )
            try:
                run_successful_transfer_tests(
                    final_browser,
                    TARGET_URL,
                    results,
                    update_result,
                    save_evidence,
                )

                # Save results before any later report generation.
                Path("qa_report_final_transfer.json").write_text(
                    json.dumps(
                        {
                            "results": [
                                item for item in results
                                if item["test_id"] in final_ids
                            ]
                        },
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                print("Final transfer evidence saved.")
            finally:
                final_browser.close()
    else:
        saved_report = Path("qa_report_final_transfer.json")
        if saved_report.exists():
            saved_data = json.loads(
                saved_report.read_text(encoding="utf-8")
            )
            saved_results = {
                item["test_id"]: item
                for item in saved_data.get("results", [])
                if item["test_id"] in final_ids
            }
            for item in results:
                if item["test_id"] in saved_results:
                    item.update(saved_results[item["test_id"]])

    # TC022_SAVED_EVIDENCE
    # Import the previously executed insufficient-funds test.
    # Do not repeat this transfer: it can create negative balances.
    tc022_path = BASE / "tc022_result.json"

    if tc022_path.exists():
        try:
            evidence = json.loads(
                tc022_path.read_text(encoding="utf-8")
            )

            before = evidence["balances_before"]
            after = evidence["balances_after"]
            status_code = evidence["response_status"]

            checking_before = before[CHECKING_ID]
            checking_after = after[CHECKING_ID]

            if status_code == 409 and before == after:
                test_status = "PASS"
                details = (
                    "Insufficient-funds transfer rejected with "
                    "HTTP 409; account balances unchanged."
                )
            elif status_code == 201 and before != after:
                test_status = "FAIL"
                details = (
                    "DB-QA-002: Insufficient-funds transfer was "
                    "accepted with HTTP 201. Checking balance "
                    f"changed from {checking_before} to "
                    f"{checking_after}. "
                    "Expected HTTP 409 and unchanged balances."
                )
            else:
                test_status = "UNVERIFIED"
                details = (
                    "Saved transfer response requires manual review. "
                    f"HTTP status: {status_code}."
                )

            update_result(
                results,
                "TC-022",
                test_status,
                details,
                str(tc022_path),
            )

            print(f"TC-022: {test_status} (saved evidence)")

        except Exception as error:
            print(f"TC-022 evidence import error: {error}")

    summary = {
        "total": len(results),
        "passed": sum(
            result["status"] == "PASS"
            for result in results
        ),
        "failed": sum(
            result["status"] == "FAIL"
            for result in results
        ),
        "unverified": sum(
            result["status"] == "UNVERIFIED"
            for result in results
        ),
    }

    report = {
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "target_url": TARGET_URL or None,
        "results": results,
        "summary": summary,
    }

    output = BASE / "qa_report.json"

    output.write_text(
        json.dumps(
            report,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\n================================")
    print("       DEMOBANK QA REPORT")
    print("================================")
    print(
        f"Total scenarios: {summary['total']}"
    )
    print(
        f"PASS: {summary['passed']}"
    )
    print(
        f"FAIL: {summary['failed']}"
    )
    print(
        f"UNVERIFIED: {summary['unverified']}"
    )
    print("================================")
    print(
        f"Report saved: {output}"
    )


if __name__ == "__main__":
    run()
