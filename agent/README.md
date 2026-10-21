# DemoBank Automated QA Pipeline

## Overview

An automated, specification-driven QA workflow for the DemoBank banking application.

The system extracts structured requirements from the product specification, generates test scenarios, executes browser and database checks, captures screenshots, and produces a JSON QA report.

## Final Results

| Metric | Result |
|---|---:|
| Total scenarios | 42 |
| Passed | 38 |
| Failed | 4 |
| Unverified | 0 |
| Pass rate | 90.5% |
| Confirmed defects | 4 |

## Architecture

PRD -> prd_parser.py -> requirements.json -> test_generator.py -> test_plan.json -> qa_executor.py -> qa_report.json + evidence/

The execution pipeline combines Playwright browser automation, application API checks, and PostgreSQL ledger verification.

## Technologies

- Python
- Playwright
- React and Vite
- FastAPI
- PostgreSQL
- JSON reporting

## Main Files

- prd_parser.py: Requirements extraction
- test_generator.py: Test scenario generation
- qa_executor.py: Main QA runner
- dashboard_session_tests.py: Dashboard and session tests
- transfer_validation_tests.py: Transfer validation
- transfer_feedback_tests.py: Transfer feedback tests
- successful_transfer_tests.py: Controlled transfer verification
- remaining_ui_tests.py: Navigation and UI checks
- requirements.json: Extracted requirements
- test_plan.json: Generated test scenarios
- qa_report.json: Final test results
- qa_report_final_transfer.json: Saved transfer test results
- DEFECTS.md: Four confirmed defects
- evidence/: Screenshots

## Running the Application

Follow the setup instructions in the test-website directory.

Verified local configuration:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- PostgreSQL: localhost:5433
- Database: demobank

## Running the Tests

From the agent directory, with the application running and Python dependencies installed:

    python qa_executor.py

The normal runner reuses saved evidence for the controlled transfer tests.

To intentionally execute a new successful-transfer test:

    QA_RUN_FINAL_TRANSFER=1 python qa_executor.py

WARNING: The opt-in transfer test changes account balances and transaction records. Use only against a disposable local database with a verified backup.

## Confirmed Defects

1. TC-031: End-date filtering excludes transactions on the selected end date.
2. TC-022: Transfers exceeding available funds are accepted.
3. TC-018: Zero-dollar transfers are accepted.
4. TC-019: Negative-dollar transfers are accepted.

See DEFECTS.md for details and evidence.

## Verification and Limitations

A controlled $1 transfer verified transaction creation, account balance changes, double-entry ledger records, success feedback, and persistence after refresh.

The database was restored after the controlled test.

TC-024 verifies ledger entries for both accounts in PostgreSQL, but does not independently inspect both account-history screens.

The pipeline uses deterministic automation. It does not claim autonomous LLM planning during test execution.

## API and Token Cost Audit

The deterministic QA execution path does not require paid LLM API calls.

Estimated paid LLM API/token cost for that execution path: $0.

This excludes development assistance, local infrastructure, and other unmeasured services.

## Suggested Demo Walkthrough

1. Introduce the DemoBank application.
2. Show extracted requirements and the test plan.
3. Explain browser, API, and PostgreSQL verification.
4. Show the final 42-test report.
5. Demonstrate the four confirmed defects and screenshots.
6. Explain controlled transfer testing and database restoration.

## QA Audit Report

The complete test execution audit, defect findings, evidence verification, and API/token cost estimates are available in [AUDIT_REPORT.md](AUDIT_REPORT.md).
