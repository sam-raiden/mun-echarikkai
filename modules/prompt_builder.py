"""
modules/prompt_builder.py

Responsible for constructing a fully structured reasoning prompt string
to be passed to an LLM. Injects all available context — farmer input,
entities, weather, market data, and risk categories — into a strict
template that enforces an exact output format from the LLM.

No business logic. No scoring. No API calls. No LLM interaction.
"""

from typing import Optional


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _format_context(context: dict) -> str:
    """
    Format the DecisionContext dictionary into a readable key-value block.

    Args:
        context (dict): DecisionContext with entity fields.

    Returns:
        str: A formatted multi-line string of context fields.
    """
    fields = [
        ("Crop",                 context.get("crop")),
        ("Month",                context.get("month")),
        ("Location",             context.get("location")),
        ("Irrigation",           context.get("irrigation")),
        ("Market Dependency",    context.get("market_dependency")),
        ("Financial Dependency", context.get("financial_dependency")),
    ]
    lines = []
    for label, value in fields:
        display = value if value is not None else "Unknown"
        lines.append(f"  {label:<25}: {display}")
    return "\n".join(lines)


def _format_weather(weather: dict) -> str:
    """
    Format the weather summary dictionary into a readable block.

    Args:
        weather (dict): Weather summary with temperature, rainfall, wind_speed.

    Returns:
        str: A formatted multi-line string of weather values.
    """
    def fmt(value: object, unit: str) -> str:
        return f"{value} {unit}" if value is not None else "Unavailable"

    return (
        f"  Temperature : {fmt(weather.get('temperature'), '°C')}\n"
        f"  Rainfall    : {fmt(weather.get('rainfall'), 'mm')}\n"
        f"  Wind Speed  : {fmt(weather.get('wind_speed'), 'km/h')}"
    )


def _format_market(market: dict) -> str:
    """
    Format the market context dictionary into a readable block.

    Args:
        market (dict): Market context with price_trend, volatility, demand_level.

    Returns:
        str: A formatted multi-line string of market values.
    """
    def fmt(value: object) -> str:
        return str(value).capitalize() if value is not None else "Unknown"

    return (
        f"  Price Trend  : {fmt(market.get('price_trend'))}\n"
        f"  Volatility   : {fmt(market.get('volatility'))}\n"
        f"  Demand Level : {fmt(market.get('demand_level'))}"
    )


def _format_risks(categories: list[str]) -> str:
    """
    Format the list of detected risk categories into a readable block.

    Args:
        categories (list[str]): List of risk category label strings.

    Returns:
        str: A bulleted list of risks, or a no-risk message if empty.
    """
    if not categories:
        return "  None detected."
    return "\n".join(f"  • {risk}" for risk in categories)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_prompt(
    context: dict,
    weather: dict,
    market: dict,
    categories: list[str],
    original_text: str,
) -> str:
    """
    Construct a fully structured reasoning prompt for an LLM, injecting all
    available farmer context, weather data, market intelligence, and detected
    risk categories.

    The prompt enforces a strict output format that the LLM must follow
    exactly. The format instruction is embedded in the prompt and repeated
    to reduce deviation.

    Injected sections
    -----------------
    - Original farmer input (raw text as provided)
    - DecisionContext (crop, month, location, irrigation, dependencies)
    - Weather summary (temperature, rainfall, wind speed)
    - Market context (price trend, volatility, demand level)
    - Detected risk categories (from risk_categorizer)

    Required LLM output format
    --------------------------
    The LLM must respond with exactly this structure and no other text::

        HIGH_RISKS:
        * <risk description>

        MEDIUM_RISKS:
        * <risk description>

        ASSUMPTIONS:
        * <assumption made due to missing data>

        MITIGATION:
        * <actionable mitigation step>

        RISK_SCORE: <integer between 1 and 10>
        CONFIDENCE_LEVEL: <low, medium, or high>

    Args:
        context (dict): DecisionContext dictionary produced by
            ``entity_extractor.extract_entities``. Expected keys:
            ``"crop"``, ``"month"``, ``"location"``, ``"irrigation"``,
            ``"market_dependency"``, ``"financial_dependency"``.
            Missing keys are rendered as ``"Unknown"``.
        weather (dict): Weather summary from
            ``weather_service.get_weather_summary``. Expected keys:
            ``"temperature"``, ``"rainfall"``, ``"wind_speed"``.
            ``None`` values are rendered as ``"Unavailable"``.
        market (dict): Market context from
            ``market_service.get_market_context``. Expected keys:
            ``"price_trend"``, ``"volatility"``, ``"demand_level"``.
            ``None`` values are rendered as ``"Unknown"``.
        categories (list[str]): Ordered list of risk category labels from
            ``risk_categorizer.categorize_risks``.
        original_text (str): The raw normalized farmer input string as
            received after ``ingestion.normalize_input``.

    Returns:
        str: A fully constructed prompt string ready to be sent to an LLM.
            The string is non-empty and contains all injected sections.

    Raises:
        TypeError: If any argument is not of its expected type.
        ValueError: If ``original_text`` is empty or whitespace-only.

    Examples:
        >>> prompt = build_prompt(
        ...     context={"crop": "rice", "month": "june", "location": "tamil_nadu",
        ...              "irrigation": "rainfed", "market_dependency": None,
        ...              "financial_dependency": "loan"},
        ...     weather={"temperature": 31.4, "rainfall": 0.0, "wind_speed": 14.2},
        ...     market={"price_trend": "stable", "volatility": "low", "demand_level": "high"},
        ...     categories=["Weather Risk", "Financial Risk"],
        ...     original_text="i grow rice in tamil nadu rainfed in june with kcc loan"
        ... )
        >>> isinstance(prompt, str)
        True
        >>> "HIGH_RISKS:" in prompt
        True
        >>> "RISK_SCORE:" in prompt
        True
    """
    # --- Type guards ---
    if not isinstance(context, dict):
        raise TypeError(f"context must be a dict, got {type(context).__name__!r}.")
    if not isinstance(weather, dict):
        raise TypeError(f"weather must be a dict, got {type(weather).__name__!r}.")
    if not isinstance(market, dict):
        raise TypeError(f"market must be a dict, got {type(market).__name__!r}.")
    if not isinstance(categories, list):
        raise TypeError(f"categories must be a list, got {type(categories).__name__!r}.")
    if not isinstance(original_text, str):
        raise TypeError(f"original_text must be a str, got {type(original_text).__name__!r}.")
    if not original_text.strip():
        raise ValueError("original_text must not be empty or whitespace-only.")

    # --- Build prompt sections ---
    context_block: str = _format_context(context)
    weather_block: str = _format_weather(weather)
    market_block: str  = _format_market(market)
    risks_block: str   = _format_risks(categories)

    prompt: str = f"""You are an expert agricultural risk analyst specializing in Indian farming systems.
Analyze the following farmer profile and provide a structured risk assessment.

════════════════════════════════════════════════════════
FARMER INPUT
════════════════════════════════════════════════════════
{original_text.strip()}

════════════════════════════════════════════════════════
DECISION CONTEXT
════════════════════════════════════════════════════════
{context_block}

════════════════════════════════════════════════════════
WEATHER CONDITIONS
════════════════════════════════════════════════════════
{weather_block}

════════════════════════════════════════════════════════
MARKET INTELLIGENCE
════════════════════════════════════════════════════════
{market_block}

════════════════════════════════════════════════════════
PRE-DETECTED RISK CATEGORIES
════════════════════════════════════════════════════════
{risks_block}

════════════════════════════════════════════════════════
INSTRUCTIONS
════════════════════════════════════════════════════════
Using ALL the information above, produce a detailed risk assessment.

STRICT RULES — YOU MUST FOLLOW THESE EXACTLY:
1. Respond ONLY with the output format below. No introduction. No explanation. No extra text.
2. Every section header must appear EXACTLY as shown — same spelling, same caps, same colon.
3. Every item must start with * (asterisk + space).
4. RISK_SCORE must be a single integer from 1 (very low risk) to 10 (extremely high risk).
5. CONFIDENCE_LEVEL must be exactly one word: low, medium, or high.
6. If a section has no items, write: * None
7. Do not add any section not listed below.
8. Do not include any text before HIGH_RISKS: or after CONFIDENCE_LEVEL value.

════════════════════════════════════════════════════════
REQUIRED OUTPUT FORMAT — DO NOT DEVIATE
════════════════════════════════════════════════════════
HIGH_RISKS:
* <describe each high severity risk on its own line>

MEDIUM_RISKS:
* <describe each medium severity risk on its own line>

ASSUMPTIONS:
* <list any assumption made due to missing or unclear data>

MITIGATION:
* <list one actionable mitigation step per line>

RISK_SCORE: <single integer 1-10>
CONFIDENCE_LEVEL: <low or medium or high>
════════════════════════════════════════════════════════
YOUR RESPONSE MUST START WITH: HIGH_RISKS:
════════════════════════════════════════════════════════"""

    return prompt


# ---------------------------------------------------------------------------
# Manual smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sample_context = {
        "crop": "rice",
        "month": "june",
        "location": "tamil_nadu",
        "irrigation": "rainfed",
        "market_dependency": None,
        "financial_dependency": "loan",
    }
    sample_weather = {
        "temperature": 31.4,
        "rainfall": 0.0,
        "wind_speed": 14.2,
    }
    sample_market = {
        "price_trend": "stable",
        "volatility": "low",
        "demand_level": "high",
    }
    sample_categories = ["Weather Risk", "Resource Risk", "Financial Risk"]
    sample_text = "i grow rice in tamil nadu using rainfed irrigation in june with kcc loan"

    prompt = build_prompt(
        context=sample_context,
        weather=sample_weather,
        market=sample_market,
        categories=sample_categories,
        original_text=sample_text,
    )

    print(prompt)