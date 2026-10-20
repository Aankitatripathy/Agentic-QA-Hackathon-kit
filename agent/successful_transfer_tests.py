import json
import subprocess
import getpass
from decimal import Decimal
from playwright.sync_api import expect

PSQL = "/Applications/Postgres.app/Contents/Versions/16/bin/psql"

CHECKING = "00000000-0000-0000-0000-000000000101"
SAVINGS = "00000000-0000-0000-0000-000000000102"

MEMO = "QA-FINAL-TRANSFER-ONE-DOLLAR"


def query_db(sql):
    result = subprocess.run(
        [
            PSQL,
            "-h", "localhost",
            "-p", "5433",
            "-U", getpass.getuser(),
            "-d", "demobank",
            "-t", "-A",
            "-c", sql,
        ],
        capture_output=True,
        text=True,
        timeout=20,
        check=True,
    )
    return result.stdout.strip()


def run_successful_transfer_tests(
    browser, base_url, results, update_result, save_evidence
):
    context = browser.new_context()
    page = context.new_page()

    test_ids = [
        "TC-014", "TC-023", "TC-024", "TC-025", "TC-027"
    ]

    def record(test_id, passed, details):
        screenshot = save_evidence(
            page, f"{test_id}_successful_transfer.png"
        )
        update_result(
            results,
            test_id,
            "PASS" if passed else "FAIL",
            details,
            screenshot,
        )
        print(f"{test_id}: {'PASS' if passed else 'FAIL'}")

    def unverified(test_id, details):
        update_result(
            results, test_id, "UNVERIFIED", details
        )
        print(f"{test_id}: UNVERIFIED ({details})")

    try:
        # Prevent accidental duplicate test execution.
        previous = query_db(
            "SELECT COUNT(*) FROM transactions "
            f"WHERE memo = '{MEMO}';"
        )

        if int(previous) != 0:
            for test_id in test_ids:
                unverified(
                    test_id,
                    "Final test transfer already exists. "
                    "Restore the database before rerunning."
                )
            return

        before = query_db(
            "SELECT id, balance FROM accounts ORDER BY id;"
        )

        before_balances = {
            row.split("|")[0]: Decimal(row.split("|")[1])
            for row in before.splitlines()
        }

        if (
            before_balances.get(CHECKING) != Decimal("4369.75")
            or before_balances.get(SAVINGS) != Decimal("8275.00")
        ):
            for test_id in test_ids:
                unverified(
                    test_id,
                    "Unexpected starting balances. "
                    "Transfer was not attempted."
                )
            return

        before_transactions = int(
            query_db("SELECT COUNT(*) FROM transactions;")
        )

        before_entries = int(
            query_db(
                "SELECT COUNT(*) FROM transaction_entries;"
            )
        )

        print("\nStarting one controlled $1.00 transfer")

        page.goto(base_url)
        page.get_by_role(
            "button", name="Enter Demo"
        ).click()

        page.wait_for_url(
            "**/dashboard", timeout=15000
        )

        page.goto(f"{base_url}/transfer")

        expect(
            page.get_by_role(
                "heading",
                name="Transfer between your accounts",
            )
        ).to_be_visible(timeout=15000)

        page.locator("#source").select_option(CHECKING)
        page.locator("#destination").select_option(SAVINGS)
        page.locator("#amount").fill("1.00")
        page.locator("#memo").fill(MEMO)

        with page.expect_response(
            lambda response:
                "/api/transfers" in response.url
                and response.request.method == "POST",
            timeout=20000,
        ) as transfer_response:
            page.get_by_role(
                "button", name="Transfer funds"
            ).click()

        response = transfer_response.value
        print(f"Transfer API status: {response.status}")

        expect(
            page.get_by_role(
                "button", name="Transfer funds"
            )
        ).to_be_enabled(timeout=20000)

        after = query_db(
            "SELECT id, balance FROM accounts ORDER BY id;"
        )

        after_balances = {
            row.split("|")[0]: Decimal(row.split("|")[1])
            for row in after.splitlines()
        }

        matching = query_db(
            "SELECT id, type, status, amount, memo "
            "FROM transactions "
            f"WHERE memo = '{MEMO}';"
        )

        rows = [
            row.split("|")
            for row in matching.splitlines()
            if row.strip()
        ]

        exactly_one = len(rows) == 1

        record(
            "TC-014",
            exactly_one and rows[0][2] == "completed",
            f"Transfer rows={len(rows)}; "
            f"status={rows[0][2] if rows else 'missing'}",
        )

        transfer_id = rows[0][0] if exactly_one else None

        if transfer_id:
            entries = query_db(
                "SELECT account_id, amount_delta "
                "FROM transaction_entries "
                f"WHERE transaction_id = '{transfer_id}';"
            )

            entry_rows = [
                row.split("|")
                for row in entries.splitlines()
                if row.strip()
            ]

            entry_map = {
                account_id: Decimal(delta)
                for account_id, delta in entry_rows
            }
        else:
            entry_rows = []
            entry_map = {}

        after_transactions = int(
            query_db("SELECT COUNT(*) FROM transactions;")
        )

        after_entries = int(
            query_db(
                "SELECT COUNT(*) FROM transaction_entries;"
            )
        )

        atomic = (
            after_balances[CHECKING]
            == before_balances[CHECKING] - Decimal("1.00")
            and after_balances[SAVINGS]
            == before_balances[SAVINGS] + Decimal("1.00")
            and entry_map.get(CHECKING) == Decimal("-1.00")
            and entry_map.get(SAVINGS) == Decimal("1.00")
            and len(entry_rows) == 2
            and after_transactions == before_transactions + 1
            and after_entries == before_entries + 2
        )

        record(
            "TC-023",
            atomic,
            f"Checking {before_balances[CHECKING]} -> "
            f"{after_balances[CHECKING]}; "
            f"Savings {before_balances[SAVINGS]} -> "
            f"{after_balances[SAVINGS]}; "
            f"ledger entries={entry_rows}; "
            f"transaction count={after_transactions}; "
            f"entry count={after_entries}",
        )

        histories = (
            query_db(
                "SELECT COUNT(DISTINCT account_id) "
                "FROM transaction_entries "
                f"WHERE transaction_id = '{transfer_id}';"
            )
            if transfer_id else "0"
        )

        record(
            "TC-024",
            histories == "2"
            and exactly_one
            and rows[0][3] == "1.00"
            and rows[0][4] == MEMO,
            f"Distinct accounts with transfer entries={histories}; "
            f"memo={MEMO}; transfer ID={transfer_id}. "
            "Verified via database ledger.",
        )

        try:
            expect(
                page.get_by_text(
                    "Transfer complete", exact=False
                )
            ).to_be_visible(timeout=10000)
            success_visible = True
        except Exception:
            success_text = page.locator("body").inner_text()
            success_visible = (
                "Transfer successful" in success_text
                or "Transfer completed" in success_text
            )

        record(
            "TC-025",
            success_visible and exactly_one,
            f"Success message visible={success_visible}; "
            f"committed transaction exists={exactly_one}",
        )

        page.reload()

        expect(
            page.get_by_role(
                "heading",
                name="Transfer between your accounts",
            )
        ).to_be_visible(timeout=15000)

        persisted = query_db(
            "SELECT COUNT(*) FROM transactions "
            f"WHERE memo = '{MEMO}' AND status = 'completed';"
        ) == "1"

        persisted_balances = query_db(
            "SELECT id, balance FROM accounts ORDER BY id;"
        )

        same_balances = (
            persisted_balances.strip() == after.strip()
        )

        record(
            "TC-027",
            persisted and same_balances,
            f"Transfer persists={persisted}; "
            f"balances unchanged after refresh={same_balances}",
        )

        print(
            "\nFINAL TRANSFER COMPLETE. "
            "Do not rerun until database restoration."
        )

    except Exception as error:
        print(f"Final transfer test error: {error}")
        for test_id in test_ids:
            if next(
                (
                    item for item in results
                    if item["test_id"] == test_id
                    and item["status"] != "UNVERIFIED"
                ),
                None,
            ) is None:
                unverified(test_id, str(error))

    finally:
        context.close()
