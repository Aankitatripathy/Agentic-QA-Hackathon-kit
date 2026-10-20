
from pathlib import Path
import json
import re

# Locate the DemoBank PRD relative to this script.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PRD_PATH = PROJECT_ROOT / "test-website" / "PRD.md"
OUTPUT_PATH = Path(__file__).resolve().parent / "requirements.json"


def extract_requirements(prd_text):
    requirements = []
    section = "General"

    for line in prd_text.splitlines():
        line = line.strip()

        if line.startswith("## "):
            section = line[3:].strip()

        elif re.match(r"^-\s+", line):
            requirement = re.sub(r"^-\s+", "", line).strip()

            if requirement:
                requirements.append({
                    "id": f"REQ-{len(requirements) + 1:03d}",
                    "section": section,
                    "requirement": requirement,
                    "status": "UNVERIFIED"
                })

    return requirements


def main():
    if not PRD_PATH.exists():
        raise FileNotFoundError(
            f"PRD not found at: {PRD_PATH}"
        )

    prd_text = PRD_PATH.read_text(encoding="utf-8")
    requirements = extract_requirements(prd_text)

    OUTPUT_PATH.write_text(
        json.dumps(requirements, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"PRD loaded: {PRD_PATH}")
    print(f"Extracted {len(requirements)} candidate requirements.")
    print(f"Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
