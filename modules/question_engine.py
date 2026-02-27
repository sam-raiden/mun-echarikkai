"""
modules/question_engine.py

Responsible for identifying missing critical fields in a DecisionContext and
returning adaptive follow-up questions for each gap.

No external calls, no context mutation, no enrichment, no UI logic.
"""

from typing import Optional


# ---------------------------------------------------------------------------
# Field → follow-up question mapping (immutable constant, not global state)
# ---------------------------------------------------------------------------

_FIELD_QUESTIONS: dict[str, str] = {
    "crop": "Which crop are you planning to grow this season?",
    "month": "Which month are you planning to start or are currently in?",
    "location": "Which state or district is your farm located in?",
    "irrigation": (
        "What is the irrigation status of your farm? "
        "(e.g. irrigated, rainfed, or partially irrigated)"
    ),
}

# Ordered list of critical fields to check — order determines question priority.
_CRITICAL_FIELDS: list[str] = ["crop", "month", "location", "irrigation"]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def identify_missing_fields(context: dict) -> list[str]:
    """
    Identify missing critical fields in a DecisionContext and return a list
    of adaptive follow-up questions for each absent or null field.

    Critical fields checked (in priority order):
        - ``crop``      – the primary crop being cultivated
        - ``month``     – the calendar month of the plan
        - ``location``  – the farm's state or region
        - ``irrigation``– irrigation status of the farm

    A field is considered missing if:
        * The key is absent from ``context``, **or**
        * The key's value is ``None``, **or**
        * The key's value is an empty string after stripping whitespace.

    The function does **not** mutate ``context`` in any way.

    Args:
        context (dict): A DecisionContext dictionary, typically produced by
            ``entity_extractor.extract_entities``. Expected keys include at
            minimum: ``"crop"``, ``"month"``, ``"location"``,
            ``"irrigation"``, ``"market_dependency"``,
            ``"financial_dependency"``. Extra keys are silently ignored.

    Returns:
        list[str]: An ordered list of follow-up question strings, one per
            missing critical field. Returns an empty list if all critical
            fields are present and non-empty.

    Raises:
        TypeError: If ``context`` is not a ``dict``.

    Examples:
        >>> identify_missing_fields({
        ...     "crop": "rice",
        ...     "month": None,
        ...     "location": "",
        ...     "irrigation": "rainfed",
        ... })
        [
            'Which month are you planning to start or are currently in?',
            'Which state or district is your farm located in?',
        ]

        >>> identify_missing_fields({
        ...     "crop": "wheat",
        ...     "month": "june",
        ...     "location": "punjab",
        ...     "irrigation": "irrigated",
        ... })
        []

        >>> identify_missing_fields({})
        [
            'Which crop are you planning to grow this season?',
            'Which month are you planning to start or are currently in?',
            'Which state or district is your farm located in?',
            'What is the irrigation status of your farm? ...',
        ]
    """
    if not isinstance(context, dict):
        raise TypeError(
            f"context must be a dict, got {type(context).__name__!r}."
        )

    questions: list[str] = []

    for field in _CRITICAL_FIELDS:
        value: Optional[str] = context.get(field)
        is_missing: bool = (
            value is None
            or (isinstance(value, str) and not value.strip())
        )
        if is_missing:
            questions.append(_FIELD_QUESTIONS[field])

    return questions