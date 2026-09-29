from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent

ANSWERS_FILE = (
    PROJECT_ROOT
    / "answers.golden.jsonl"
)

EXPECTED_FILE = (
    PROJECT_ROOT
    / "cases"
    / "golden_eval.jsonl"
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    records = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON on line {line_number} "
                    f"in {path}: {exc}"
                ) from exc

            records.append(record)

    return records


def regex_matches(pattern: str, text: str) -> bool:
    try:
        return re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        ) is not None
    except re.error as exc:
        print(
            f"WARNING: Invalid regex {pattern!r}: {exc}",
            file=sys.stderr,
        )
        return False


def evaluate_case(
    expected: dict[str, Any],
    actual: dict[str, Any],
) -> tuple[bool, list[str]]:
    failures: list[str] = []

    expected_route = expected["expected_route"]
    actual_route = actual.get("route")

    if actual_route != expected_route:
        failures.append(
            f"route: expected {expected_route!r}, "
            f"got {actual_route!r}"
        )

    answer = actual.get("answer", "")

    if not isinstance(answer, str):
        failures.append("answer is not a string")
        answer = ""

    for pattern in expected.get("must_include", []):
        if not regex_matches(pattern, answer):
            failures.append(
                f"missing required pattern: {pattern!r}"
            )

    for pattern in expected.get("must_not_include", []):
        if regex_matches(pattern, answer):
            failures.append(
                f"forbidden pattern found: {pattern!r}"
            )

    return not failures, failures


def main() -> int:
    expected_records = load_jsonl(EXPECTED_FILE)
    actual_records = load_jsonl(ANSWERS_FILE)

    actual_by_id = {
        record.get("id"): record
        for record in actual_records
    }

    print()
    print("Golden Visible Evaluation")
    print("=========================")
    print()

    passed = 0
    failed = 0

    for expected in expected_records:
        case_id = expected["id"]
        actual = actual_by_id.get(case_id)

        if actual is None:
            print(f"{case_id}: FAIL")
            print("  Missing answer for this case.")
            print()
            failed += 1
            continue

        success, failures = evaluate_case(
            expected,
            actual,
        )

        if success:
            print(f"{case_id}: PASS")
            passed += 1
        else:
            print(f"{case_id}: FAIL")

            for failure in failures:
                print(f"  - {failure}")

            print()
            failed += 1

    print()
    print("-------------------------")
    print(f"Passed: {passed}/{len(expected_records)}")
    print(f"Failed: {failed}/{len(expected_records)}")
    print("-------------------------")
    print()

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())