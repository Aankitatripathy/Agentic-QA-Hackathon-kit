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

## Installation and Reproduction Guide

### Prerequisites

- Python 3.11 or newer
- Node.js 20 or newer and npm
- Docker with Docker Compose
- PostgreSQL 16 (provided by the database Docker setup)

### 1. Start the DemoBank database

From the repository root:

    cd test-website/database
    make up

The original database configuration uses localhost:5432.
The verified local QA environment used localhost:5433.
Ensure the backend DATABASE_URL matches the port exposed by PostgreSQL.

Database setup details: test-website/database/README.md.

### 2. Start the backend

Open a separate terminal, navigate to test-website/backend, and run:

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -e .
    cp .env.example .env

Edit .env to configure DATABASE_URL and a random SESSION_SECRET.
Then run:

    set -a; source .env; set +a
    uvicorn demobank.main:app --host 0.0.0.0 --port 8000 --reload

Verify the backend at http://localhost:8000/health.

### 3. Start the frontend

Open another terminal, navigate to test-website/frontend, and run:

    npm install
    npm run dev

Open http://localhost:5173.

### 4. Install the QA agent

Open another terminal, navigate to the agent directory, and run:

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt
    python -m playwright install chromium

### 5. Execute the QA suite

With the database, backend, and frontend running:

    python qa_executor.py

The default runner reuses saved evidence for the controlled successful-transfer tests.
Do not enable QA_RUN_FINAL_TRANSFER unless using a disposable database with a verified backup.

### 6. Review the results

- requirements.json: Extracted requirements
- test_plan.json: Generated QA scenarios
- qa_report.json: Main test results
- qa_report_final_transfer.json: Saved successful-transfer results
- DEFECTS.md: Confirmed defects
- AUDIT_REPORT.md: Test coverage, execution results, evidence, and limitations
- evidence/: Browser screenshots

The completed evaluation reports 42 scenarios: 38 PASS, 4 FAIL, and 0 UNVERIFIED.

