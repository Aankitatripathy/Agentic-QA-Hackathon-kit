# DemoBank Automated QA Audit Report

## 1. Executive Summary

This report documents the results of the specification-driven DemoBank QA execution pipeline.

- Total test scenarios: **42**
- Passed: **38**
- Failed: **4**
- Unverified: **0**
- Pass rate: **90.48%**
- Confirmed application defects: **4**

## 2. Test Execution and Coverage

The project uses specification-derived requirements and test scenarios with browser automation, application API assertions, and PostgreSQL verification.

| Metric | Result |
|---|---:|
| Test scenarios evaluated | 42 |
| Passed | 38 |
| Failed | 4 |
| Unverified | 0 |
| Valid screenshot references | 41 |

The full machine-readable results are available in [qa_report.json](qa_report.json).

## 3. Confirmed Defects

| Defect ID | Test ID | Finding | Status |
|---|---|---|---|
| DB-QA-003 | TC-018 | Zero-dollar transfer accepted | FAIL |
| DB-QA-004 | TC-019 | Negative transfer accepted | FAIL |
| DB-QA-002 | TC-022 | Insufficient-funds transfer accepted | FAIL |
| DB-QA-001 | TC-031 | Inclusive end-date filtering incorrect | FAIL |

### Observed Failure Details

**TC-018**

Amount='0'; HTTP 201; balances unchanged=True; no success message=False; response={"transaction":{"id":"25aa01e5-7598-4df6-a7a6-7e7ccce10f33","type":"transfer","status":"completed","amount":"0.00","memo":null,"occurred_at":"2026-10-20T06:21:20.466068Z","source_account":{"id":"00000000-0000-0000-0000-000000000101","name":"Everyday Checking","masked_number":"•••• 1042"},"destinatio

**TC-019**

Amount='-10'; HTTP 201; balances unchanged=False; no success message=False; response={"transaction":{"id":"4cf0bfdb-1fc7-45c4-911b-86df0480b984","type":"transfer","status":"completed","amount":"-10.00","memo":null,"occurred_at":"2026-10-20T06:21:20.682992Z","source_account":{"id":"00000000-0000-0000-0000-000000000101","name":"Everyday Checking","masked_number":"•••• 1042"},"destinat

**TC-022**

DB-QA-002: Insufficient-funds transfer was accepted with HTTP 201. Checking balance changed from 4369.75 to -100.00. Expected HTTP 409 and unchanged balances.

**TC-031**

BUG DB-QA-001: Annual bonus (+$950.00) occurred on June 15, 2025, but was excluded when the start and end dates were both June 15, 2025. The PRD requires inclusive date boundaries in Pacific Time.

See [DEFECTS.md](DEFECTS.md) for reproduction steps, expected behavior, and actual behavior.

## 4. Evidence Audit

- Main report: **41 valid screenshot references**.
- TC-022 has recorded HTTP response and balance-change evidence in the test result, but no screenshot attachment.
- The final-transfer report contains five passing saved results with five valid screenshot references.
- Evidence paths are relative to the agent directory.
- Evidence files are stored under [evidence/](evidence/).

## 5. API and Token Cost Audit

| Cost category | Estimate | Basis |
|---|---|---|
| Paid LLM API calls during deterministic QA execution | 0 | No paid LLM API required by this execution path |
| Paid LLM input/output tokens during QA execution | 0 | No paid LLM API required by this execution path |
| Estimated paid LLM API cost | $0.00 | Deterministic execution only |
| Browser, database, and local compute | Not measured | Local environment |
| Development assistance costs | Not measured | Excluded from execution estimate |

The $0.00 estimate applies only to paid LLM API usage in the deterministic QA execution path. It is not a claim that the entire project had zero development or operating cost.

## 6. Execution Safety and Limitations

- Transfer tests can modify application database balances.
- A controlled successful-transfer run was performed and its results were saved separately.
- The test database was restored after the controlled run.
- The pipeline is specification-driven and deterministic; it does not claim autonomous LLM planning during execution.
- TC-022 does not have a screenshot attachment.
- Full reproduction requires the DemoBank application, PostgreSQL, Python dependencies, and browser tooling.

## 7. Audit Artifacts

- [Requirements](requirements.json)
- [Test plan](test_plan.json)
- [Complete QA report](qa_report.json)
- [Final-transfer results](qa_report_final_transfer.json)
- [Confirmed defects](DEFECTS.md)
- [Execution instructions](README.md)

## 8. Conclusion

All 42 planned scenarios received a recorded outcome. The execution identified four application defects and preserved supporting results and available evidence.
