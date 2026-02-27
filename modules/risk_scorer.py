"""
modules/risk_scorer.py

Responsible for applying deterministic rule-based adjustments to a base
risk score produced by the LLM. No LLM calls, no external services, no
business logic beyond the specified adjustment rules.

Score is always clamped between 1 and 10.
"""

from typing import Optional


def adjust_risk_score(base_score: int, context: dict, weather: dict) -> int:
    """
    Apply deterministic rule-based adjustments to a base risk score and
    return a final clamped integer score between 1 and 10.

    Adjustment rules applied in order
    ----------------------------------
    +1  If ``context["irrigation"]`` is ``None`` or equals ``"none"`` —
        indicates no confirmed water source.
    +1  If ``weather["rainfall"]`` is not ``None`` and equals ``0`` —
        indicates zero rainfall recorded, increasing drought risk.
    +1  If ``context["financial_dependency"]`` equals ``"loan"`` —
        indicates active debt exposure.

    The score is clamped to the range [1, 10] after all adjustments.
    Input arguments are never modified.

    Args:
        base_score (int): The initial risk score, typically extracted from
            the LLM response by ``formatter.parse_llm_response``. Must be
            an integer.
        context (dict): DecisionContext dictionary produced by
            ``entity_extractor.extract_entities``. Expected keys:
            ``"irrigation"``, ``"financial_dependency"``. Missing keys are
            treated as ``None``.
        weather (dict): Weather summary from
            ``weather_service.get_weather_summary``. Expected key:
            ``"rainfall"``. Missing key is treated as ``None``.

    Returns:
        int: Final adjusted risk score clamped between 1 and 10 inclusive.

    Raises:
        TypeError: If ``base_score`` is not an ``int``.
        TypeError: If ``context`` is not a ``dict``.
        TypeError: If ``weather`` is not a ``dict``.

    Examples:
        >>> adjust_risk_score(5, {"irrigation": None, "financial_dependency": "loan"}, {"rainfall": 0})
        8

        >>> adjust_risk_score(9, {"irrigation": None, "financial_dependency": "loan"}, {"rainfall": 0})
        10

        >>> adjust_risk_score(5, {"irrigation": "irrigated", "financial_dependency": None}, {"rainfall": 10.0})
        5

        >>> adjust_risk_score(1, {}, {})
        1
    """
    # --- Type guards ---
    if not isinstance(base_score, int):
        raise TypeError(
            f"base_score must be an int, got {type(base_score).__name__!r}."
        )
    if not isinstance(context, dict):
        raise TypeError(
            f"context must be a dict, got {type(context).__name__!r}."
        )
    if not isinstance(weather, dict):
        raise TypeError(
            f"weather must be a dict, got {type(weather).__name__!r}."
        )

    score: int = base_score

    # --- Rule 1: No confirmed irrigation source ---
    irrigation: Optional[str] = context.get("irrigation")
    if irrigation is None or (isinstance(irrigation, str) and irrigation.strip().lower() == "none"):
        score += 1

    # --- Rule 2: Zero rainfall recorded ---
    rainfall: Optional[float] = weather.get("rainfall")
    if rainfall is not None and rainfall == 0:
        score += 1

    # --- Rule 3: Active loan dependency ---
    financial_dependency: Optional[str] = context.get("financial_dependency")
    if isinstance(financial_dependency, str) and financial_dependency.strip().lower() == "loan":
        score += 1

    # --- Clamp between 1 and 10 ---
    return max(1, min(10, score))


# ---------------------------------------------------------------------------
# Manual smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        # (base_score, context, weather, expected_label)
        (5, {"irrigation": None, "financial_dependency": "loan"}, {"rainfall": 0},    "5 + 3 = 8"),
        (9, {"irrigation": None, "financial_dependency": "loan"}, {"rainfall": 0},    "9 + 3 → capped at 10"),
        (5, {"irrigation": "irrigated", "financial_dependency": None}, {"rainfall": 10.0}, "5 + 0 = 5"),
        (5, {"irrigation": "none", "financial_dependency": "loan"}, {"rainfall": 0},  "5 + 3 = 8"),
        (1, {}, {},                                                                    "1 + 0 = 1"),
        (1, {"irrigation": None, "financial_dependency": "loan"}, {"rainfall": 0},    "1 + 3 → capped min check = 4"),
    ]

    for base, ctx, wthr, label in tests:
        result = adjust_risk_score(base, ctx, wthr)
        print(f"  base={base:2d}  →  adjusted={result:2d}   ({label})")