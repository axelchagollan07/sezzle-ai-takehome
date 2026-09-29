"""
Evaluation runner for the Sezzle Support Assistant.

Required contract:

    python run_cases.py <cases.jsonl> <answers.jsonl>

Input JSONL:
    {"id": "...", "question": "...", "user_id": "..."}

Output JSONL:
    {"id": "...", "route": "...", "answer": "..."}

The runner accepts externally supplied evaluation cases so that
the same contract can be used for visible and hidden evaluations.

Routing is determined exclusively by SezzleAgent through AgentResponse.
The runner never infers routing from the generated answer.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from src.agent import AgentResponse, SezzleAgent


VALID_ROUTES = {
    "policy",
    "tool",
    "both",
    "escalate",
}


def load_cases(path: Path) -> list[dict[str, Any]]:
    """Load evaluation cases from a JSONL file."""

    if not path.exists():
        raise FileNotFoundError(
            f"Cases file not found: {path}"
        )

    cases: list[dict[str, Any]] = []

    # utf-8-sig allows files created by PowerShell with a UTF-8 BOM.
    with path.open("r", encoding="utf-8-sig") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                case = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON on line {line_number}: {exc}"
                ) from exc

            if not isinstance(case, dict):
                raise ValueError(
                    f"Line {line_number} must contain a JSON object."
                )

            required_fields = (
                "id",
                "question",
                "user_id",
            )

            missing = [
                field
                for field in required_fields
                if field not in case
            ]

            if missing:
                raise ValueError(
                    f"Line {line_number} is missing required fields: "
                    f"{', '.join(missing)}"
                )

            cases.append(case)

    return cases


def validate_agent_response(
    response: AgentResponse,
) -> AgentResponse:
    """
    Validate the structured response returned by the agent.

    The runner deliberately does not infer route from answer text.
    """

    if not isinstance(response, AgentResponse):
        raise TypeError(
            "SezzleAgent.answer() must return AgentResponse, "
            f"got {type(response).__name__}."
        )

    if response.route not in VALID_ROUTES:
        raise ValueError(
            f"Agent returned invalid route: {response.route!r}. "
            f"Expected one of: {sorted(VALID_ROUTES)}"
        )

    if not isinstance(response.answer, str):
        raise TypeError(
            "AgentResponse.answer must be a string."
        )

    answer = response.answer.strip()

    if not answer:
        raise ValueError(
            "AgentResponse.answer cannot be empty."
        )

    return AgentResponse(
        route=response.route,
        answer=answer,
    )


def write_answer(
    file,
    case_id: Any,
    response: AgentResponse,
) -> None:
    """Write one structured agent response as JSONL."""

    result = {
        "id": case_id,
        "route": response.route,
        "answer": response.answer.strip(),
    }

    file.write(
        json.dumps(
            result,
            ensure_ascii=False,
        )
        + "\n"
    )


def run_cases(
    cases_path: Path,
    answers_path: Path,
) -> None:
    """
    Run the Sezzle agent against all supplied cases.

    The agent is responsible for determining the route.
    This runner does NOT infer routing from the generated answer.
    """

    cases = load_cases(cases_path)

    print(
        f"Loaded {len(cases)} evaluation case(s) "
        f"from {cases_path}"
    )

    agent = SezzleAgent()

    successful = 0
    failed = 0

    with answers_path.open(
        "w",
        encoding="utf-8",
    ) as output_file:

        for index, case in enumerate(cases, start=1):
            case_id = case["id"]
            question = str(case["question"])
            user_id = str(case["user_id"])

            print(
                f"[{index}/{len(cases)}] "
                f"Running case {case_id}..."
            )

            try:
                # Ask the agent to process the case.
                response = agent.answer(
                    user_id=user_id,
                    message=question,
                )

                # Validate the structured AgentResponse.
                #
                # Routing comes exclusively from the agent.
                # The runner does not inspect or infer the route
                # from the generated answer.
                response = validate_agent_response(response)

                # Write the validated response.
                write_answer(
                    output_file,
                    case_id=case_id,
                    response=response,
                )

                successful += 1

                print(
                    f"  Route: {response.route}"
                )

            except Exception as exc:
                failed += 1

                # Preserve the required JSONL contract even when
                # an individual case fails.
                error_response = AgentResponse(
                    route="escalate",
                    answer=(
                        "The assistant encountered an internal error "
                        "while processing this request."
                    ),
                )

                write_answer(
                    output_file,
                    case_id=case_id,
                    response=error_response,
                )

                print(
                    f"  ERROR: {type(exc).__name__}: {exc}"
                )

    print()
    print("Evaluation complete.")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Answers written to: {answers_path}")


def print_project_status() -> None:
    """Run a basic project/data configuration check."""

    data_file = Path(
        "data/orders/DATA-orders.json"
    )

    policies_dir = Path(
        "data/policies"
    )

    print("Sezzle Support Assistant")
    print("=" * 50)

    if data_file.exists():
        try:
            with data_file.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

            print(
                f"Users loaded: "
                f"{len(data.get('users', []))}"
            )

            print(
                f"Orders loaded: "
                f"{len(data.get('orders', []))}"
            )

            print(
                f"Data date: "
                f"{data.get('today', 'unknown')}"
            )

        except Exception as exc:
            print(
                f"ERROR reading order data: "
                f"{type(exc).__name__}: {exc}"
            )
    else:
        print(
            f"ERROR: Order data not found: {data_file}"
        )

    if policies_dir.exists():
        policies = list(
            policies_dir.glob("*.md")
        )

        print(
            f"Policies loaded: {len(policies)}"
        )
    else:
        print(
            f"ERROR: Policies directory not found: "
            f"{policies_dir}"
        )

    print()
    print("Usage:")
    print(
        "  python run_cases.py "
        "<cases.jsonl> <answers.jsonl>"
    )


def main() -> None:
    """CLI entry point."""

    if len(sys.argv) == 1:
        print_project_status()
        return

    if len(sys.argv) != 3:
        print(
            "Usage: python run_cases.py "
            "<cases.jsonl> <answers.jsonl>"
        )
        sys.exit(1)

    cases_path = Path(sys.argv[1])
    answers_path = Path(sys.argv[2])

    try:
        run_cases(
            cases_path=cases_path,
            answers_path=answers_path,
        )

    except Exception as exc:
        print(
            f"ERROR: {type(exc).__name__}: {exc}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()