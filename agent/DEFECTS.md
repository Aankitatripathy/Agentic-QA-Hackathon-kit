# DemoBank QA Defect Report

## Executive Summary

The automated QA suite evaluated 42 scenarios against the DemoBank application.

| Metric | Result |
|---|---:|
| Total test scenarios | 42 |
| Passed | 38 |
| Failed | 4 |
| Unverified | 0 |
| Pass rate | 90.5% |
| Confirmed defects | 4 |

The suite uses Playwright browser automation, API observations, PostgreSQL verification, and screenshot evidence.

## Confirmed Defects

### DB-QA-001: End-date filter excludes transactions on the selected date

- **Test:** TC-031
- **Area:** Transaction history
- **Expected:** Selecting June 15, 2025 as the end date includes transactions occurring on June 15.
- **Actual:** The Annual Bonus transaction for $950 is excluded.
- **Likely cause:** The backend uses an exclusive midnight cutoff rather than the end of the selected calendar day.
- **Suggested fix:** Implement an exclusive upper bound at midnight of the following day.
- **Evidence:** `evidence/TC-031_end_date.png`

### DB-QA-002: Insufficient-funds transfer is accepted

- **Test:** TC-022
- **Area:** Transfer validation
- **Expected:** A transfer exceeding the available source-account balance is rejected.
- **Actual:** The API returns HTTP 201 and the checking account becomes overdrawn.
- **Impact:** The application permits transfers without sufficient available funds.
- **Suggested fix:** Validate the available balance atomically before committing ledger entries.
- **Evidence:** Saved test result and screenshots in `evidence/`.

### DB-QA-003: Zero-dollar transfer is accepted

- **Test:** TC-018
- **Area:** Transfer validation
- **Expected:** Transfer amounts must be greater than zero.
- **Actual:** A $0.00 transfer is accepted with HTTP 201 and completed status.
- **Suggested fix:** Enforce a strictly positive amount in the API and database validation.
- **Evidence:** Saved test result and screenshots in `evidence/`.

### DB-QA-004: Negative-dollar transfer is accepted

- **Test:** TC-019
- **Area:** Transfer validation
- **Expected:** Negative transfer amounts are rejected.
- **Actual:** A -$10.00 transfer is accepted with HTTP 201 and completed status, reversing the intended movement of funds.
- **Impact:** A malformed transfer can increase the source balance and decrease the destination balance.
- **Suggested fix:** Reject nonpositive amounts before creating any transaction or ledger entries.
- **Evidence:** Saved test result and screenshots in `evidence/`.

## Verification Method

The test runner validates browser behavior, API responses, transaction records, account balances, and double-entry ledger movements.

For the successful-transfer tests, a controlled $1.00 transfer was executed and checked against PostgreSQL. The database was subsequently restored to its original seeded state.

**Verification limitation:** TC-024 confirms ledger entries for both accounts in PostgreSQL, but does not independently inspect both rendered account-history screens.

## Artifacts

- `qa_report.json`: Complete 42-scenario report
- `qa_report_final_transfer.json`: Saved successful-transfer test results
- `requirements.json`: Extracted requirements
- `test_plan.json`: Generated test scenarios
- `evidence/`: Browser screenshots and defect evidence
