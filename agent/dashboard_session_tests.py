from decimal import Decimal
from urllib.parse import urljoin

from playwright.sync_api import expect


CHECKING_ID = "00000000-0000-0000-0000-000000000101"
SAVINGS_ID = "00000000-0000-0000-0000-000000000102"


def run_dashboard_session_tests(
    browser,
    base_url,
    results,
    update_result,
    save_evidence,
):
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()

    def record(test_id, passed, details):
        screenshot = save_evidence(
            page, f"{test_id}_dashboard_session.png"
        )
        update_result(
            results,
            test_id,
            "PASS" if passed else "FAIL",
            details,
            screenshot,
        )
        print(f"{test_id}: {'PASS' if passed else 'FAIL'}")

    def open_demo():
        page.goto(base_url)
        expect(
            page.get_by_role("button", name="Enter Demo")
        ).to_be_visible(timeout=10000)

        page.get_by_role("button", name="Enter Demo").click()

        page.wait_for_url("**/dashboard", timeout=15000)

        expect(
            page.get_by_role("heading", name="Your accounts")
        ).to_be_visible(timeout=15000)

        expect(
            page.locator('[data-testid="account-card"]')
        ).to_have_count(2, timeout=15000)

    try:
        # TC-002: Enter Demo creates a session.
        open_demo()
        record(
            "TC-002",
            page.locator(
                '[data-testid="active-customer"]'
            ).is_visible()
            and page.locator(
                '[data-testid="account-card"]'
            ).count() == 2,
            f"Authenticated dashboard loaded; URL={page.url}",
        )

        # TC-003: Customer identity and logout control.
        customer_visible = page.locator(
            '[data-testid="active-customer"]'
        ).is_visible()
        logout_visible = page.get_by_role(
            "button", name="Log out"
        ).is_visible()
        record(
            "TC-003",
            customer_visible and logout_visible,
            "Customer name and logout button displayed.",
        )

        # TC-006: Refresh preserves the active session.
        page.reload()
        expect(
            page.locator('[data-testid="active-customer"]')
        ).to_be_visible()
        record(
            "TC-006",
            "/dashboard" in page.url,
            "Active session survived page refresh.",
        )

        # TC-008: Dashboard displays two accounts.
        cards = page.locator('[data-testid="account-card"]')
        expect(cards).to_have_count(2)
        record(
            "TC-008",
            cards.count() == 2,
            "Dashboard displays checking and savings account cards.",
        )

        # TC-009: Account names, masked numbers, and currency.
        card_text = " ".join(cards.all_inner_texts())
        record(
            "TC-009",
            all(
                item in card_text
                for item in (
                    "Everyday Checking",
                    "Rainy Day Savings",
                    "USD",
                    "1042",
                )
            ),
            "Account names, masked identifiers, and USD are visible.",
        )

        # TC-010: Currency balances display two decimal places.
        balances = page.locator(
            '[data-testid="account-balance"]'
        ).all_inner_texts()
        import re
        formatted = (
            len(balances) == 2
            and all(
                re.search(r"\d{1,3}(?:,\d{3})*\.\d{2}", value)
                for value in balances
            )
        )
        record(
            "TC-010",
            formatted,
            f"Displayed balances: {balances}",
        )

        # TC-011: Full seeded account IDs are not shown.
        html_text = page.locator("body").inner_text()
        record(
            "TC-011",
            CHECKING_ID not in html_text
            and SAVINGS_ID not in html_text,
            "Full account UUIDs are not visible on the dashboard.",
        )

        # TC-012: Account details include balance and history.
        page.goto(f"{base_url}/accounts/{CHECKING_ID}")
        expect(
            page.get_by_role("heading", name="Everyday Checking")
        ).to_be_visible()
        balance_visible = page.locator(
            '[data-testid="account-balance"]'
        ).is_visible()
        history_visible = page.get_by_role(
            "heading", name="Transaction history"
        ).is_visible()
        record(
            "TC-012",
            balance_visible and history_visible,
            "Account detail displays available balance and history.",
        )

        # TC-013: Detail balance matches dashboard balance.
        detail_balance = page.locator(
            '[data-testid="account-balance"]'
        ).inner_text()
        page.goto(f"{base_url}/dashboard")
        expect(cards).to_have_count(2)
        dashboard_balance = cards.filter(
            has_text="Everyday Checking"
        ).locator('[data-testid="account-balance"]').inner_text()
        record(
            "TC-013",
            "".join(detail_balance.split()) == "".join(dashboard_balance.split()),
            f"Detail={detail_balance!r}; dashboard={dashboard_balance!r}",
        )

        # TC-004: Logout returns user to landing page.
        page.get_by_role("button", name="Log out").click()
        expect(
            page.get_by_role("button", name="Enter Demo")
        ).to_be_visible(timeout=10000)
        record(
            "TC-004",
            page.url.rstrip("/") == base_url.rstrip("/"),
            "Logout returned to landing page.",
        )

        # TC-005: Protected page cannot be opened after logout.
        page.goto(f"{base_url}/dashboard")
        expect(
            page.get_by_role("button", name="Enter Demo")
        ).to_be_visible(timeout=10000)
        record(
            "TC-005",
            "/dashboard" not in page.url,
            "Protected dashboard redirects after logout.",
        )

        # TC-007: Refresh does not restore a logged-out session.
        page.reload()
        expect(
            page.get_by_role("button", name="Enter Demo")
        ).to_be_visible(timeout=10000)
        record(
            "TC-007",
            page.url.rstrip("/") == base_url.rstrip("/"),
            "Logged-out session remains inactive after refresh.",
        )

    finally:
        context.close()
