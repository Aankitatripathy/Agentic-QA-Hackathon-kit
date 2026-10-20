
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent

SCENARIOS = {

    "REQ-001": [
        ("positive", "One seeded demo customer is available"),
    ],
    "REQ-003": [
        ("positive", "Header shows customer name and logout action"),
    ],
    "REQ-006": [
        ("positive", "Dashboard displays checking and savings accounts"),
    ],
    "REQ-007": [
        ("positive", "Accounts show name, type, masked ID and USD balance"),
    ],
    "REQ-009": [
        ("positive", "Account detail displays balance and related history"),
    ],
    "REQ-010": [
        ("positive", "Dashboard and detail balances remain consistent"),
    ],
    "REQ-011": [
        ("positive", "Transfer between owned accounts succeeds"),
    ],
    "REQ-012": [
        ("positive", "Transfer form contains required fields and optional memo"),
    ],
    "REQ-018": [
        ("positive", "Success message appears after committed transfer"),
        ("negative", "Failed transfer never displays success"),
    ],
    "REQ-020": [
        ("positive", "Combined and account-specific histories are available"),
    ],
    "REQ-021": [
        ("positive", "Transaction rows display required details and direction"),
    ],
    "REQ-026": [
        ("positive", "Profile displays synthetic customer details"),
    ],
    "REQ-027": [
        ("negative", "Profile does not expose sensitive or other-user data"),
    ],
    "REQ-028": [
        ("positive", "Desktop viewport 1280x800 is usable"),
        ("edge", "Narrow viewport remains usable"),
    ],
    "REQ-029": [
        ("positive", "Controls show labels and feedback states"),
    ],
    "REQ-030": [
        ("edge", "Pending action prevents accidental duplicate submission"),
    ],
    "REQ-031": [
        ("positive", "Navigation links open their labeled destinations"),
    ],
    "REQ-032": [
        ("negative", "Recoverable error allows retry or dashboard return"),
    ],

    "REQ-002": [
        ("positive", "Enter Demo opens dashboard without login"),
    ],
    "REQ-004": [
        ("positive", "Logout returns to landing page"),
        ("negative", "Protected page cannot be accessed after logout"),
    ],
    "REQ-005": [
        ("edge", "Refresh preserves an active demo session"),
        ("negative", "Refresh does not restore a logged-out session"),
    ],
    "REQ-008": [
        ("positive", "Balances display two decimal places"),
        ("negative", "Full account numbers are not exposed"),
    ],
    "REQ-013": [
        ("negative", "Same-account transfer is rejected without side effects"),
    ],
    "REQ-014": [
        ("negative", "Blank transfer amount is rejected"),
        ("negative", "Zero transfer amount is rejected"),
        ("negative", "Negative transfer amount is rejected"),
        ("negative", "Nonnumeric transfer amount is rejected"),
        ("edge", "More than two decimal places is rejected"),
    ],
    "REQ-015": [
        ("negative", "Insufficient-funds transfer is rejected"),
    ],
    "REQ-016": [
        ("positive", "Valid transfer debits and credits exactly once"),
    ],
    "REQ-017": [
        ("positive", "Completed transfer appears in both account histories"),
    ],
    "REQ-019": [
        ("positive", "Transfer persists after refresh"),
    ],
    "REQ-022": [
        ("positive", "Transaction filters work together"),
    ],
    "REQ-023": [
        ("edge", "End-date filter includes transactions on the selected date"),
        ("edge", "Start-date filter includes transactions on the selected date"),
    ],
    "REQ-024": [
        ("edge", "No matching transactions displays an empty state"),
    ],
    "REQ-025": [
        ("positive", "Clear filters restores all transactions"),
    ],
}

def main():
    requirements = json.loads(
        (BASE / "requirements.json").read_text(encoding="utf-8")
    )

    tests = []
    covered_ids = set()

    for requirement in requirements:
        req_id = requirement["id"]

        if requirement["section"] == "Out of scope":
            continue

        for category, title in SCENARIOS.get(req_id, []):
            tests.append({
                "test_id": f"TC-{len(tests) + 1:03d}",
                "requirement_id": req_id,
                "category": category,
                "title": title,
                "expected": requirement["requirement"],
                "status": "UNVERIFIED"
            })
            covered_ids.add(req_id)

    output = {
        "tests": tests,
        "planned_requirement_ids": sorted(covered_ids),
        "unplanned_requirement_ids": [
            r["id"] for r in requirements
            if r["section"] != "Out of scope"
            and r["id"] not in covered_ids
        ]
    }

    path = BASE / "test_plan.json"
    path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"Generated {len(tests)} test scenarios.")
    print(f"Requirements with planned tests: {len(covered_ids)}")
    print(
        "Requirements needing more scenarios:",
        len(output["unplanned_requirement_ids"])
    )
    print(f"Saved: {path}")


if __name__ == "__main__":
    main()
