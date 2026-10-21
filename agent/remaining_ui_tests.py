import re
from playwright.sync_api import expect

CHECKING_ID = "00000000-0000-0000-0000-000000000101"


def run_remaining_ui_tests(
    browser, base_url, results, update_result, save_evidence
):
    context = browser.new_context(
        viewport={"width": 1280, "height": 800}
    )
    page = context.new_page()

    def record(test_id, passed, details):
        screenshot = save_evidence(
            page, f"{test_id}_remaining_ui.png"
        )
        update_result(
            results,
            test_id,
            "PASS" if passed else "FAIL",
            details,
            screenshot,
        )
        print(f"{test_id}: {'PASS' if passed else 'FAIL'}")

    def execute(test_id, action):
        try:
            passed, details = action()
            record(test_id, passed, details)
        except Exception as error:
            print(f"{test_id}: UNVERIFIED ({error})")
            try:
                screenshot = save_evidence(
                    page, f"{test_id}_execution_error.png"
                )
            except Exception:
                screenshot = None
            update_result(
                results, test_id, "UNVERIFIED",
                f"Test execution error: {error}", screenshot
            )

    def visit(path, heading=None):
        page.goto(f"{base_url}{path}")
        if heading:
            expect(
                page.get_by_role("heading", name=heading)
            ).to_be_visible(timeout=15000)

    try:
        visit("/")
        page.get_by_role("button", name="Enter Demo").click()
        page.wait_for_url("**/dashboard", timeout=15000)
        expect(
            page.locator('[data-testid="account-card"]')
        ).to_have_count(2, timeout=15000)

        # TC-001: Customer exists, but uniqueness needs database proof.
        def tc001():
            visit("/profile", "Your profile")
            name = page.locator(
                '[data-testid="profile-name"]'
            ).inner_text().strip()
            return (
                bool(name),
                f"Seeded customer accessible: {name}. "
                "This UI check does not independently prove "
                "that only one customer exists."
            )

        # TC-001: Verify seeded-customer count directly in PostgreSQL.
        try:
            from db_helper import query_db

            customer_count = int(
                query_db("SELECT COUNT(*) FROM customers;", timeout=15)
            )
            record(
                "TC-001",
                customer_count == 1,
                f"PostgreSQL customers table contains "
                f"{customer_count} seeded customer(s).",
            )
        except Exception as error:
            update_result(
                results,
                "TC-001",
                "UNVERIFIED",
                f"Database verification unavailable: {error}",
            )
            print(f"TC-001: UNVERIFIED ({error})")

        def tc028():
            visit("/transactions")
            expect(
                page.locator(
                    '[data-testid="transaction-table"]'
                )
            ).to_be_visible(timeout=15000)
            combined_count = page.locator(
                '[data-testid="transaction-row"]'
            ).count()

            visit(f"/accounts/{CHECKING_ID}", "Everyday Checking")
            history_heading = page.get_by_role(
                "heading", name="Transaction history"
            )
            expect(history_heading).to_be_visible()

            visit(f"/transactions?account_id={CHECKING_ID}")
            expect(
                page.locator('[data-testid="transaction-table"]')
            ).to_be_visible(timeout=15000)

            account_count = page.locator(
                '[data-testid="transaction-row"]'
            ).count()

            return (
                combined_count > 0 and account_count > 0,
                f"Combined history rows={combined_count}; "
                f"account-specific rows={account_count}; "
                f"URL={page.url}"
            )

        execute("TC-028", tc028)

        def tc035():
            visit("/profile", "Your profile")
            name = page.locator(
                '[data-testid="profile-name"]'
            ).inner_text().strip()
            email = page.locator(
                '[data-testid="profile-email"]'
            ).inner_text().strip()
            return (
                bool(name) and bool(email)
                and "synthetic" in page.locator(
                    "body"
                ).inner_text().lower(),
                f"Profile name={name!r}; masked email={email!r}"
            )

        execute("TC-035", tc035)

        def tc036():
            visit("/profile", "Your profile")
            text = page.locator("body").inner_text()
            email = page.locator(
                '[data-testid="profile-email"]'
            ).inner_text().strip()
            masked = "*" in email or "•" in email
            no_uuid = CHECKING_ID not in text
            no_secret_labels = not re.search(
                r"(?im)^\s*(password|access token|secret key)\s*:",
                text,
            )
            return (
                masked and no_uuid and no_secret_labels,
                f"Email masked={masked}; account UUID absent={no_uuid}; "
                f"no visible secret fields={no_secret_labels}. "
                "This checks rendered profile data, not network leakage."
            )

        execute("TC-036", tc036)

        def tc037():
            page.set_viewport_size({"width": 1280, "height": 800})
            visit("/dashboard")
            expect(
                page.locator('[data-testid="account-card"]')
            ).to_have_count(2)
            no_overflow = page.evaluate(
                "() => document.documentElement.scrollWidth <= "
                "document.documentElement.clientWidth + 2"
            )
            return (
                no_overflow,
                f"Desktop 1280x800; horizontal overflow={not no_overflow}"
            )

        execute("TC-037", tc037)

        def tc038():
            page.set_viewport_size({"width": 375, "height": 812})
            visit("/dashboard")
            expect(
                page.locator('[data-testid="account-card"]')
            ).to_have_count(2)
            no_overflow = page.evaluate(
                "() => document.documentElement.scrollWidth <= "
                "document.documentElement.clientWidth + 2"
            )
            cards_visible = all(
                card.is_visible()
                for card in page.locator(
                    '[data-testid="account-card"]'
                ).all()
            )
            return (
                no_overflow and cards_visible,
                f"Mobile 375x812; cards visible={cards_visible}; "
                f"horizontal overflow={not no_overflow}"
            )

        execute("TC-038", tc038)

        def tc039():
            page.set_viewport_size({"width": 1280, "height": 800})
            visit("/transfer", "Transfer between your accounts")
            labeled = all(
                page.locator(f'label[for="{field}"]').count() == 1
                for field in ("source", "destination", "amount", "memo")
            )
            page.locator("#amount").fill("")
            page.get_by_role(
                "button", name="Transfer funds"
            ).click()
            error_visible = page.locator(
                "#amount-error"
            ).is_visible()
            return (
                labeled and error_visible,
                f"All four inputs labeled={labeled}; "
                f"validation feedback visible={error_visible}"
            )

        execute("TC-039", tc039)

        def tc041():
            visit("/dashboard")
            destinations = [
                ("Transactions", "/transactions"),
                ("Transfer", "/transfer"),
                ("Profile", "/profile"),
                ("Dashboard", "/dashboard"),
            ]
            visited = []
            for label, path in destinations:
                page.get_by_role(
                    "navigation", name="Main"
                ).get_by_role("link", name=label).click()
                page.wait_for_url(
                    f"**{path}", timeout=15000
                )
                visited.append(path)
            return (
                len(visited) == 4,
                f"Navigation destinations visited: {visited}"
            )

        execute("TC-041", tc041)

        def tc042():
            def fail_transactions(route):
                route.fulfill(
                    status=503,
                    content_type="application/json",
                    body='{"error":{"code":"temporarily_unavailable",'
                         '"message":"Temporary test outage"}}',
                )

            page.route("**/api/transactions?*", fail_transactions)
            page.route("**/api/transactions", fail_transactions)

            try:
                visit("/transactions")

                expect(
                    page.get_by_role(
                        "link", name="Back to dashboard"
                    )
                ).to_be_visible(timeout=15000)

                retry_visible = page.get_by_role(
                    "button", name="Try again"
                ).is_visible()

                page.get_by_role(
                    "link", name="Back to dashboard"
                ).click()

                page.wait_for_url(
                    "**/dashboard", timeout=15000
                )

                return (
                    retry_visible,
                    "Simulated transaction API outage displayed "
                    "retry and dashboard-return controls."
                )
            finally:
                page.unroute(
                    "**/api/transactions?*", fail_transactions
                )
                page.unroute(
                    "**/api/transactions", fail_transactions
                )

        execute("TC-042", tc042)

    finally:
        context.close()
