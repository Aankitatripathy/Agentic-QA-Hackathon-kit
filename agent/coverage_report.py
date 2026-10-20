
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent

requirements = json.loads(
    (BASE / "requirements.json").read_text(encoding="utf-8")
)

plan = json.loads(
    (BASE / "test_plan.json").read_text(encoding="utf-8")
)

tests = plan["tests"]

print("\nDEMOBANK QA TEST COVERAGE")
print("=" * 55)

for req in requirements:
    if req["section"] == "Out of scope":
        continue

    matching = [
        test for test in tests
        if test["requirement_id"] == req["id"]
    ]

    status = "PLANNED" if matching else "MISSING"

    print(f"{req['id']} | {status} | {req['section']}")

print("\nSUMMARY")
print("-" * 55)

in_scope = [
    req for req in requirements
    if req["section"] != "Out of scope"
]

covered = {
    test["requirement_id"] for test in tests
}

print(f"Total requirements: {len(in_scope)}")
print(f"Requirements with tests: {len(covered)}")
print(f"Requirements without tests: {len(in_scope) - len(covered)}")
print(f"Total test scenarios: {len(tests)}")
print(f"Planning coverage: {len(covered) / len(in_scope) * 100:.1f}%")
