"""
app.py  —  Mun-Echarikkai system runner (development test)

Run this file to see all 7 modules working together:
    py app.py
"""

# ── import all modules ──────────────────────────────────────────────────────
from modules.ingestion import normalize_input
from modules.entity_extractor import extract_entities
from modules.question_engine import identify_missing_fields
from modules.risk_categorizer import categorize_risks
from modules.weather_service import get_weather_summary
from modules.market_service import get_market_context
from modules.prompt_builder import build_prompt
from modules.llm_service import call_llm
from modules.formatter import parse_llm_response
from modules.risk_scorer import adjust_risk_score


def run_pipeline(raw_input: str) -> None:
    """Run the full Mun-Echarikkai pipeline on a raw input string."""

    print("\n" + "=" * 60)
    print("🌾  MUN-ECHARIKKAI  —  Farm Decision Support System")
    print("=" * 60)

    # ── STEP 1: Normalize input ──────────────────────────────────
    print("\n📥  STEP 1 — Normalize Input")
    clean_text = normalize_input("text", raw_input)
    print(f"    Raw   : {raw_input!r}")
    print(f"    Clean : {clean_text!r}")

    # ── STEP 2: Extract entities ─────────────────────────────────
    print("\n🔍  STEP 2 — Extract Entities")
    context = extract_entities(clean_text)
    for key, value in context.items():
        print(f"    {key:<25} : {value}")

    # ── STEP 3: Identify missing fields ──────────────────────────
    print("\n❓  STEP 3 — Missing Field Questions")
    questions = identify_missing_fields(context)
    if questions:
        for q in questions:
            print(f"    → {q}")
    else:
        print("    ✅ All critical fields are present.")

    # ── STEP 4: Categorize risks ──────────────────────────────────
    print("\n⚠️   STEP 4 — Risk Categories")
    categories = categorize_risks(context)
    if categories:
        for r in categories:
            print(f"    ⚠  {r}")
    else:
        print("    ✅ No risks detected.")

    # ── STEP 5: Weather ───────────────────────────────────────────
    print("\n🌦️   STEP 5 — Weather Summary  (Chennai coords)")
    weather = get_weather_summary(13.0827, 80.2707)
    print(f"    Temperature : {weather['temperature']} °C")
    print(f"    Rainfall    : {weather['rainfall']} mm")
    print(f"    Wind Speed  : {weather['wind_speed']} km/h")
    print("    (None = network not available in this environment)")

    # ── STEP 6: Market context ────────────────────────────────────
    print("\n📊  STEP 6 — Market Context")
    crop = context.get("crop")
    if crop:
        market = get_market_context(crop)
        print(f"    Crop        : {crop}")
        print(f"    Price Trend : {market['price_trend']}")
        print(f"    Volatility  : {market['volatility']}")
        print(f"    Demand      : {market['demand_level']}")
    else:
        market = {"price_trend": None, "volatility": None, "demand_level": None}
        print("    ⚠  No crop detected — skipping market lookup.")

    # ── STEP 7: LLM Risk Reasoning ───────────────────────────────
    print("\n🤖  STEP 7 — LLM Risk Reasoning")
    prompt = build_prompt(
        context=context,
        weather=weather,
        market=market,
        categories=categories,
        original_text=raw_input,
    )
    response = call_llm(prompt)
    parsed = parse_llm_response(response)

    print("\n  🔴  High Risks:")
    for item in parsed["high_risks"]:
        print(f"      • {item}")
    if not parsed["high_risks"]:
        print("      None")

    print("\n  🟡  Medium Risks:")
    for item in parsed["medium_risks"]:
        print(f"      • {item}")
    if not parsed["medium_risks"]:
        print("      None")

    print("\n  📋  Assumptions:")
    for item in parsed["assumptions"]:
        print(f"      • {item}")
    if not parsed["assumptions"]:
        print("      None")

    print("\n  🛡️   Mitigation:")
    for item in parsed["mitigation"]:
        print(f"      • {item}")
    if not parsed["mitigation"]:
        print("      None")

    base_score: int = parsed["risk_score"] if parsed["risk_score"] else 5
    final_score: int = adjust_risk_score(
        base_score=base_score,
        context=context,
        weather=weather,
    )

    print(f"\n  📊  Risk Score     : {parsed['risk_score']} / 10")
    print(f"  🎯  Confidence     : {parsed['confidence_level']}")
    print(f"  📊  Final Adjusted Risk Score : {final_score} / 10")

    print("\n" + "=" * 60 + "\n")


# ── Test with two example inputs ────────────────────────────────────────────
if __name__ == "__main__":

    run_pipeline(
        "I am growing rice in Tamil Nadu using borewell irrigation in June. "
        "I have taken a KCC loan."
    )

    run_pipeline(
        "Cotton farmer in Maharashtra. Rainfed. Sells in mandi. No loan."
    )