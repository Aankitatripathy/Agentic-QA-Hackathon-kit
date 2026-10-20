from playwright.sync_api import expect


def run_transfer_feedback_tests(
    browser, base_url, results, update_result, save_evidence
):
    context = browser.new_context()
    page = context.new_page()

    def record(test_id, passed, details):
        screenshot = save_evidence(
            page, f"{test_id}_transfer_feedback.png"
        )
        update_result(
            results,
            test_id,
            "PASS" if passed else "FAIL",
            details,
            screenshot,
        )
        print(f"{test_id}: {'PASS' if passed else 'FAIL'}")

    def prepare_form():
        page.goto(base_url)
        page.get_by_role("button", name="Enter Demo").click()
        page.wait_for_url("**/dashboard", timeout=15000)
        page.goto(f"{base_url}/transfer")

        expect(page.locator("#source")).to_be_enabled(timeout=15000)
        expect(page.locator("#destination")).to_be_enabled()

        source = page.locator("#source").input_value()
        destination = page.locator("#destination").input_value()

        assert source and destination and source != destination, (
            "Two distinct accounts must be selected"
        )

        page.locator("#amount").fill("1.00")
        page.locator("#memo").fill("Automated feedback test")

    try:
        print("\nRunning TC-026: Rejected transfer feedback")

        def reject_transfer(route):
            route.fulfill(
                status=409,
                content_type="application/json",
                body='{"code":"insufficient_funds",'
                     '"message":"Transfer rejected for QA testing."}',
            )

        page.route("**/api/transfers", reject_transfer)

        try:
            prepare_form()

            page.get_by_role(
                "button", name="Transfer funds"
            ).click()

            expect(
                page.get_by_text("Transfer not completed")
            ).to_be_visible(timeout=15000)

            error_visible = page.get_by_text(
                "No money was moved."
            ).is_visible()

            receipt_absent = page.get_by_text(
                "Transfer complete", exact=False
            ).count() == 0

            record(
                "TC-026",
                error_visible and receipt_absent,
                "Simulated HTTP 409 rejection; "
                f"failure explanation visible={error_visible}; "
                f"success receipt absent={receipt_absent}. "
                "Request intercepted; no money moved.",
            )

        except Exception as error:
            update_result(
                results, "TC-026", "UNVERIFIED",
                f"Test execution error: {error}"
            )
            print(f"TC-026: UNVERIFIED ({error})")

        finally:
            page.unroute("**/api/transfers", reject_transfer)

        print("\nRunning TC-040: Duplicate submission prevention")

        requests_seen = []

        def hold_transfer(route):
            requests_seen.append(route)
            # Deliberately keep the request pending.
            # The route is aborted after assertions.

        page.route("**/api/transfers", hold_transfer)

        try:
            prepare_form()

            submit = page.get_by_role(
                "button", name="Transfer funds"
            )

            submit.click()

            pending_button = page.get_by_role(
                "button", name="Submitting transfer…"
            )

            expect(pending_button).to_be_disabled(timeout=15000)

            busy = page.locator(
                "form.transfer-form"
            ).get_attribute("aria-busy") == "true"

            pending_button.dispatch_event("click")
            page.wait_for_timeout(300)

            record(
                "TC-040",
                busy and len(requests_seen) == 1,
                f"Form aria-busy={busy}; "
                f"intercepted POST requests={len(requests_seen)}; "
                "submit button disabled while pending.",
            )

        except Exception as error:
            update_result(
                results, "TC-040", "UNVERIFIED",
                f"Test execution error: {error}"
            )
            print(f"TC-040: UNVERIFIED ({error})")

        finally:
            for route in requests_seen:
                try:
                    route.abort()
                except Exception:
                    pass

            page.unroute("**/api/transfers", hold_transfer)

    finally:
        context.close()
