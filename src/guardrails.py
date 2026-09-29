"""
Guardrails for the Sezzle support agent.

The LLM is not trusted with authorization decisions.
This module contains deterministic checks that must happen
outside the model.
"""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class GuardrailResult:
    """Result of a deterministic safety check."""

    allowed: bool
    reason: str | None = None


class Guardrails:
    """
    Deterministic safety layer around the LLM.

    Responsibilities:
    - detect obvious prompt injection attempts
    - detect requests for unauthorized order information
    - prevent the agent from claiming unsupported actions
    - keep security-sensitive decisions outside the model
    """

    PROMPT_INJECTION_PATTERNS = (
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"ignore\s+(all\s+)?prior\s+instructions",
        r"disregard\s+(all\s+)?previous\s+instructions",
        r"forget\s+(all\s+)?previous\s+instructions",
        r"reveal\s+(your\s+)?system\s+prompt",
        r"show\s+(me\s+)?your\s+system\s+prompt",
        r"developer\s+message",
        r"system\s+instructions",
        r"bypass\s+(your\s+)?rules",
        r"override\s+(your\s+)?rules",
    )

    def validate_input(self, question: str) -> GuardrailResult:
        """
        Validate the user's raw question before sending it to the LLM.
        """

        if not question or not question.strip():
            return GuardrailResult(
                allowed=False,
                reason="EMPTY_QUESTION",
            )

        normalized = question.lower().strip()

        for pattern in self.PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, normalized):
                return GuardrailResult(
                    allowed=False,
                    reason="PROMPT_INJECTION",
                )

        return GuardrailResult(allowed=True)

    @staticmethod
    def extract_order_ids(text: str) -> list[str]:
        """
        Extract order IDs mentioned in a user message.

        Example:
            "What happened to ord_3002?"

        returns:
            ["ord_3002"]
        """

        if not text:
            return []

        return re.findall(
            r"\bord_\d+\b",
            text.lower(),
        )

    def validate_order_access(
        self,
        user_id: str,
        requested_order_ids: list[str],
        orders_repository,
    ) -> GuardrailResult:
        """
        Verify that every explicitly requested order belongs to the user.

        The LLM never makes this authorization decision.
        """

        for order_id in requested_order_ids:
            try:
                orders_repository.get_order_for_user(
                    user_id,
                    order_id,
                )
            except ValueError as exc:
                if str(exc) == "ORDER_NOT_FOUND":
                    return GuardrailResult(
                        allowed=False,
                        reason="ORDER_NOT_FOUND",
                    )

                if str(exc) == "ORDER_NOT_AUTHORIZED":
                    return GuardrailResult(
                        allowed=False,
                        reason="ORDER_NOT_AUTHORIZED",
                    )

                return GuardrailResult(
                    allowed=False,
                    reason="ORDER_ACCESS_ERROR",
                )

        return GuardrailResult(allowed=True)

    @staticmethod
    def build_safe_refusal(reason: str) -> str:
        """
        Return a user-facing response for deterministic guardrail failures.

        These responses do not require the LLM.
        """

        messages = {
            "EMPTY_QUESTION": (
                "Please provide a question so I can help you."
            ),
            "PROMPT_INJECTION": (
                "I can help with Sezzle support questions, "
                "but I can't follow requests to bypass my instructions "
                "or security controls."
            ),
            "ORDER_NOT_FOUND": (
                "I couldn't find that order. "
                "Please check the order ID and try again."
            ),
            "ORDER_NOT_AUTHORIZED": (
                "I can't provide information about that order "
                "because it isn't associated with your account."
            ),
            "ORDER_ACCESS_ERROR": (
                "I couldn't safely verify access to that order. "
                "Please contact support for assistance."
            ),
        }

        return messages.get(
            reason,
            "I can't safely complete that request.",
        )