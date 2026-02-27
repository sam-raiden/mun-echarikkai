"""
modules/entity_extractor.py

Responsible for extracting structured entities from normalized plan text.
Uses rule-based keyword detection only. No external services, no scoring,
no LLM calls, no business logic beyond entity identification.
"""

import re
from typing import Optional


# ---------------------------------------------------------------------------
# Keyword registries – defined at module level as immutable constants so they
# can be reused across calls without becoming mutable global state.
# Each registry maps a canonical value → list of trigger keywords/phrases.
# ---------------------------------------------------------------------------

_CROP_KEYWORDS: dict[str, list[str]] = {
    "rice": ["rice", "paddy", "samba", "kuruvai", "thaladi"],
    "wheat": ["wheat"],
    "maize": ["maize", "corn"],
    "sugarcane": ["sugarcane", "sugar cane"],
    "cotton": ["cotton"],
    "groundnut": ["groundnut", "peanut"],
    "soybean": ["soybean", "soya"],
    "tomato": ["tomato"],
    "onion": ["onion"],
    "banana": ["banana"],
    "mango": ["mango"],
    "turmeric": ["turmeric"],
    "chilli": ["chilli", "chili", "red pepper"],
    "pulses": ["pulses", "dal", "lentil", "moong", "urad", "toor", "arhar"],
    "vegetables": ["vegetables", "greens", "leafy"],
}

_MONTH_KEYWORDS: dict[str, list[str]] = {
    "january": ["january", "jan"],
    "february": ["february", "feb"],
    "march": ["march", "mar"],
    "april": ["april", "apr"],
    "may": ["may"],
    "june": ["june", "jun"],
    "july": ["july", "jul"],
    "august": ["august", "aug"],
    "september": ["september", "sep", "sept"],
    "october": ["october", "oct"],
    "november": ["november", "nov"],
    "december": ["december", "dec"],
}

_LOCATION_KEYWORDS: dict[str, list[str]] = {
    "tamil_nadu": ["tamil nadu", "tamilnadu"],
    "andhra_pradesh": ["andhra pradesh", "andhra", "ap"],
    "telangana": ["telangana"],
    "karnataka": ["karnataka"],
    "kerala": ["kerala"],
    "maharashtra": ["maharashtra"],
    "gujarat": ["gujarat"],
    "rajasthan": ["rajasthan"],
    "punjab": ["punjab"],
    "haryana": ["haryana"],
    "uttar_pradesh": ["uttar pradesh", "up"],
    "madhya_pradesh": ["madhya pradesh", "mp"],
    "west_bengal": ["west bengal"],
    "odisha": ["odisha", "orissa"],
    "bihar": ["bihar"],
    "assam": ["assam"],
    "delhi": ["delhi"],
}

_IRRIGATION_KEYWORDS: dict[str, list[str]] = {
    "irrigated": [
        "irrigated", "irrigation", "canal", "borewell", "bore well",
        "well water", "drip", "sprinkler", "pump", "tank fed", "river fed",
    ],
    "rainfed": [
        "rainfed", "rain fed", "rain-fed", "depends on rain",
        "dependent on rain", "monsoon", "no irrigation",
    ],
    "partially_irrigated": [
        "partially irrigated", "partial irrigation", "supplemental irrigation",
        "mixed irrigation",
    ],
}

_MARKET_DEPENDENCY_KEYWORDS: dict[str, list[str]] = {
    "high": [
        "market dependent", "sells in market", "market price",
        "price fluctuation", "mandi", "wholesale market", "export",
        "price risk", "market risk", "dependent on market",
    ],
    "low": [
        "self consumption", "self-consumption", "own use", "subsistence",
        "not market dependent", "local use",
    ],
    "medium": [
        "partly sells", "partial market", "some market", "local market",
        "village market",
    ],
}

_FINANCIAL_DEPENDENCY_KEYWORDS: dict[str, list[str]] = {
    "loan": [
        "loan", "credit", "borrowed", "debt", "kcc", "kisan credit",
        "bank loan", "microfinance", "moneylender", "money lender",
        "owe", "repay", "installment",
    ],
    "subsidy": [
        "subsidy", "government support", "pm kisan", "scheme", "grant",
        "free input", "aided",
    ],
    "self_funded": [
        "self funded", "self-funded", "own funds", "no loan", "no credit",
        "savings", "own investment",
    ],
    "insurance": [
        "insurance", "pmfby", "crop insurance", "insured",
    ],
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _match_first(text: str, registry: dict[str, list[str]]) -> Optional[str]:
    """
    Return the canonical key of the first registry entry whose keyword is
    found as a whole-word match in ``text``, or ``None`` if no match found.

    Args:
        text (str): Lowercased, normalized input text to search within.
        registry (dict[str, list[str]]): Mapping of canonical label to a list
            of keyword/phrase triggers.

    Returns:
        Optional[str]: The canonical label of the first match, or ``None``.
    """
    for canonical, keywords in registry.items():
        for keyword in keywords:
            # Use word-boundary anchors for single-word keywords;
            # for multi-word phrases, a plain substring search is sufficient.
            if " " in keyword:
                if keyword in text:
                    return canonical
            else:
                pattern = rf"\b{re.escape(keyword)}\b"
                if re.search(pattern, text):
                    return canonical
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_entities(plan_text: str) -> dict[str, Optional[str]]:
    """
    Extract structured agricultural entities from a normalized plan text string.

    Uses rule-based keyword matching only. No external services, no scoring,
    and no LLM inference are performed. All keys are always present in the
    returned dictionary; undetected entities are set to ``None``.

    Extracted entities
    ------------------
    crop
        The primary crop mentioned (e.g. ``"rice"``, ``"wheat"``).
    month
        The calendar month referenced (e.g. ``"june"``).
    location
        The Indian state or region detected (e.g. ``"tamil_nadu"``).
    irrigation
        Irrigation status: ``"irrigated"``, ``"rainfed"``, or
        ``"partially_irrigated"``.
    market_dependency
        Degree of market reliance: ``"high"``, ``"medium"``, or ``"low"``.
    financial_dependency
        Primary financial arrangement: ``"loan"``, ``"subsidy"``,
        ``"self_funded"``, or ``"insurance"``.

    Args:
        plan_text (str): A normalized (lowercased, whitespace-collapsed) plain
            text description of a farming plan. Must be a non-empty string.

    Returns:
        dict[str, Optional[str]]: A dictionary with exactly the following keys:
            ``"crop"``, ``"month"``, ``"location"``, ``"irrigation"``,
            ``"market_dependency"``, ``"financial_dependency"``.
            Each value is either a matched canonical string or ``None``.

    Raises:
        TypeError: If ``plan_text`` is not a ``str``.
        ValueError: If ``plan_text`` is empty or whitespace-only.

    Examples:
        >>> extract_entities("i grow rice in tamil nadu using borewell in june")
        {
            'crop': 'rice',
            'month': 'june',
            'location': 'tamil_nadu',
            'irrigation': 'irrigated',
            'market_dependency': None,
            'financial_dependency': None,
        }

        >>> extract_entities("wheat farmer in punjab rainfed taken a kcc loan")
        {
            'crop': 'wheat',
            'month': None,
            'location': 'punjab',
            'irrigation': 'rainfed',
            'market_dependency': None,
            'financial_dependency': 'loan',
        }
    """
    if not isinstance(plan_text, str):
        raise TypeError(
            f"plan_text must be a str, got {type(plan_text).__name__!r}."
        )
    if not plan_text.strip():
        raise ValueError("plan_text must not be empty or whitespace-only.")

    # Work on a lowercased copy; caller should already pass normalized text
    # but we defensively lowercase here to keep the function self-contained.
    text: str = plan_text.lower()

    result: dict[str, Optional[str]] = {
        "crop": None,
        "month": None,
        "location": None,
        "irrigation": None,
        "market_dependency": None,
        "financial_dependency": None,
    }

    result["crop"] = _match_first(text, _CROP_KEYWORDS)
    result["month"] = _match_first(text, _MONTH_KEYWORDS)
    result["location"] = _match_first(text, _LOCATION_KEYWORDS)
    result["irrigation"] = _match_first(text, _IRRIGATION_KEYWORDS)
    result["market_dependency"] = _match_first(text, _MARKET_DEPENDENCY_KEYWORDS)
    result["financial_dependency"] = _match_first(text, _FINANCIAL_DEPENDENCY_KEYWORDS)

    return result