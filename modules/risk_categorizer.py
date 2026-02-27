"""
modules/risk_categorizer.py

Responsible for mapping structured DecisionContext fields to risk categories.
All logic is deterministic and rule-based. No scoring, no LLM, no external
calls, no business logic beyond risk categorization.
"""

from typing import Optional


# ---------------------------------------------------------------------------
# Risk category constants
# ---------------------------------------------------------------------------

WEATHER_RISK: str = "Weather Risk"
RESOURCE_RISK: str = "Resource Risk"
MARKET_RISK: str = "Market Risk"
FINANCIAL_RISK: str = "Financial Risk"
OPERATIONAL_RISK: str = "Operational Risk"


# ---------------------------------------------------------------------------
# Domain knowledge tables (immutable, module-level constants)
# ---------------------------------------------------------------------------

# Maps crop → set of months considered in-season.
# Months outside this set trigger a Weather Risk for seasonal misalignment.
_CROP_SEASON_MAP: dict[str, set[str]] = {
    "rice": {
        "june", "july", "august", "september",          # Kharif (main)
        "november", "december", "january",               # Rabi / Samba
    },
    "wheat": {"october", "november", "december", "january", "february"},
    "maize": {"june", "july", "august", "september", "october"},
    "sugarcane": {"january", "february", "march", "october", "november"},
    "cotton": {"june", "july", "august", "september"},
    "groundnut": {"june", "july", "august", "september", "october"},
    "soybean": {"june", "july", "august", "september"},
    "tomato": {"october", "november", "december", "january", "february"},
    "onion": {"october", "november", "december", "january", "february"},
    "banana": {
        "january", "february", "march", "april",
        "may", "june", "july", "august",
    },
    "mango": {"january", "february", "march", "april", "may"},
    "turmeric": {"june", "july", "august"},
    "chilli": {"july", "august", "september", "october"},
    "pulses": {"june", "july", "october", "november"},
    "vegetables": {
        "october", "november", "december", "january",
        "february", "march",
    },
}

# Crops that are strongly market-price dependent by nature.
_HIGH_MARKET_CROPS: frozenset[str] = frozenset({
    "cotton", "sugarcane", "tomato", "onion", "chilli",
    "groundnut", "soybean", "mango",
})

# Financial dependency values that indicate active debt exposure.
_LOAN_DEPENDENCIES: frozenset[str] = frozenset({"loan"})

# Financial dependency values that indicate partial external reliance.
_PARTIAL_FINANCIAL_DEPS: frozenset[str] = frozenset({"subsidy", "insurance"})

# Irrigation values indicating no reliable water source.
_NO_IRRIGATION_VALUES: frozenset[str] = frozenset({"rainfed", "none", ""})

# Market dependency values mapped to risk presence.
_HIGH_MARKET_DEPENDENCY_VALUES: frozenset[str] = frozenset({"high", "medium"})


# ---------------------------------------------------------------------------
# Internal rule evaluators — each returns True if its risk category applies.
# ---------------------------------------------------------------------------

def _has_resource_risk(irrigation: Optional[str]) -> bool:
    """Return True if irrigation is absent, None, or indicates no water source."""
    if irrigation is None:
        return True
    return irrigation.strip().lower() in _NO_IRRIGATION_VALUES


def _has_weather_risk(
    crop: Optional[str],
    month: Optional[str],
    irrigation: Optional[str],
) -> bool:
    """
    Return True if:
    - crop and month are known but month falls outside the crop's season, OR
    - irrigation is rainfed (monsoon-dependent, inherently weather-exposed).
    """
    # Rainfed farming is always weather-exposed.
    if irrigation is not None and irrigation.strip().lower() == "rainfed":
        return True

    # Seasonal misalignment check.
    if crop is not None and month is not None:
        season = _CROP_SEASON_MAP.get(crop.strip().lower())
        if season is not None and month.strip().lower() not in season:
            return True

    return False


def _has_market_risk(
    crop: Optional[str],
    market_dependency: Optional[str],
) -> bool:
    """
    Return True if:
    - explicit market_dependency is high or medium, OR
    - crop is inherently market-price sensitive.
    """
    if market_dependency is not None:
        if market_dependency.strip().lower() in _HIGH_MARKET_DEPENDENCY_VALUES:
            return True

    if crop is not None and crop.strip().lower() in _HIGH_MARKET_CROPS:
        return True

    return False


def _has_financial_risk(financial_dependency: Optional[str]) -> bool:
    """Return True if the farmer is carrying active loan/debt exposure."""
    if financial_dependency is None:
        return False
    return financial_dependency.strip().lower() in _LOAN_DEPENDENCIES


def _has_operational_risk(
    crop: Optional[str],
    month: Optional[str],
    location: Optional[str],
    irrigation: Optional[str],
    financial_dependency: Optional[str],
) -> bool:
    """
    Return True if multiple context fields are unknown (None/empty), indicating
    the plan lacks sufficient definition to execute reliably, OR if partial
    financial dependency (subsidy/insurance) suggests resource gaps.
    """
    # Count how many critical fields are unresolved.
    critical_values: list[Optional[str]] = [crop, month, location, irrigation]
    missing_count: int = sum(
        1 for v in critical_values
        if v is None or (isinstance(v, str) and not v.strip())
    )
    if missing_count >= 2:
        return True

    # Subsidy/insurance reliance signals potential resource constraints.
    if financial_dependency is not None:
        if financial_dependency.strip().lower() in _PARTIAL_FINANCIAL_DEPS:
            return True

    return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def categorize_risks(context: dict) -> list[str]:
    """
    Evaluate a DecisionContext dictionary and return a deduplicated list of
    applicable risk category labels.

    Risk categories
    ---------------
    Weather Risk
        Triggered when irrigation is rainfed (monsoon-dependent) or when the
        specified month falls outside the known planting/growing season for
        the given crop.
    Resource Risk
        Triggered when irrigation status is ``None``, ``"none"``,
        ``"rainfed"``, or empty — indicating no reliable water source is
        confirmed.
    Market Risk
        Triggered when ``market_dependency`` is ``"high"`` or ``"medium"``,
        or when the crop itself is inherently price-volatile (e.g. cotton,
        onion, tomato).
    Financial Risk
        Triggered when ``financial_dependency`` is ``"loan"``, indicating
        the farmer carries active debt exposure.
    Operational Risk
        Triggered when two or more critical fields (crop, month, location,
        irrigation) are missing, or when ``financial_dependency`` is
        ``"subsidy"`` or ``"insurance"`` — indicating partial reliance on
        external support that may not materialize.

    Args:
        context (dict): A DecisionContext dictionary. Expected optional keys:
            ``"crop"``, ``"month"``, ``"location"``, ``"irrigation"``,
            ``"market_dependency"``, ``"financial_dependency"``.
            Missing keys are treated as ``None``.

    Returns:
        list[str]: An ordered, deduplicated list of risk category strings.
            Order is deterministic: Weather, Resource, Market, Financial,
            Operational. Returns an empty list if no risks are detected.

    Raises:
        TypeError: If ``context`` is not a ``dict``.

    Examples:
        >>> categorize_risks({
        ...     "crop": "rice",
        ...     "month": "june",
        ...     "location": "tamil_nadu",
        ...     "irrigation": "rainfed",
        ...     "market_dependency": None,
        ...     "financial_dependency": "loan",
        ... })
        ['Weather Risk', 'Resource Risk', 'Financial Risk']

        >>> categorize_risks({
        ...     "crop": "cotton",
        ...     "month": "july",
        ...     "location": "maharashtra",
        ...     "irrigation": "irrigated",
        ...     "market_dependency": "high",
        ...     "financial_dependency": None,
        ... })
        ['Market Risk']

        >>> categorize_risks({})
        ['Resource Risk', 'Operational Risk']
    """
    if not isinstance(context, dict):
        raise TypeError(
            f"context must be a dict, got {type(context).__name__!r}."
        )

    crop: Optional[str] = context.get("crop")
    month: Optional[str] = context.get("month")
    location: Optional[str] = context.get("location")
    irrigation: Optional[str] = context.get("irrigation")
    market_dependency: Optional[str] = context.get("market_dependency")
    financial_dependency: Optional[str] = context.get("financial_dependency")

    risks: list[str] = []

    if _has_weather_risk(crop, month, irrigation):
        risks.append(WEATHER_RISK)

    if _has_resource_risk(irrigation):
        risks.append(RESOURCE_RISK)

    if _has_market_risk(crop, market_dependency):
        risks.append(MARKET_RISK)

    if _has_financial_risk(financial_dependency):
        risks.append(FINANCIAL_RISK)

    if _has_operational_risk(crop, month, location, irrigation, financial_dependency):
        risks.append(OPERATIONAL_RISK)

    # Deduplicate while preserving deterministic order.
    seen: set[str] = set()
    unique_risks: list[str] = []
    for risk in risks:
        if risk not in seen:
            seen.add(risk)
            unique_risks.append(risk)

    return unique_risks