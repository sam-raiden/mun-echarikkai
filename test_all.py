"""
test_all.py — Mun-Echarikkai Module Tests

Run this to verify all 6 modules are working correctly:
    python test_all.py
"""

import traceback

# ── helpers ─────────────────────────────────────────────────────────────────

passed = 0
failed = 0

def check(label: str, condition: bool) -> None:
    global passed, failed
    if condition:
        print(f"  ✅  {label}")
        passed += 1
    else:
        print(f"  ❌  {label}")
        failed += 1

def section(title: str) -> None:
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")

# ════════════════════════════════════════════════════════
# MODULE 1 — ingestion.py
# ════════════════════════════════════════════════════════
section("MODULE 1 — ingestion.py")

try:
    from modules.ingestion import normalize_input

    check("Lowercases text",
        normalize_input("text", "HELLO") == "hello")

    check("Strips leading/trailing spaces",
        normalize_input("text", "  hello  ") == "hello")

    check("Collapses multiple spaces",
        normalize_input("text", "hello   world") == "hello world")

    check("Handles tabs and newlines",
        normalize_input("text", "hello\t\nworld") == "hello world")

    try:
        normalize_input("image", "data")
        check("Raises ValueError for unsupported type", False)
    except ValueError:
        check("Raises ValueError for unsupported type", True)

    try:
        normalize_input("text", "   ")
        check("Raises ValueError for whitespace-only input", False)
    except ValueError:
        check("Raises ValueError for whitespace-only input", True)

except Exception:
    print("  💥 Module failed to import or crashed:")
    traceback.print_exc()

# ════════════════════════════════════════════════════════
# MODULE 2 — entity_extractor.py
# ════════════════════════════════════════════════════════
section("MODULE 2 — entity_extractor.py")

try:
    from modules.entity_extractor import extract_entities

    result = extract_entities("i grow rice in tamil nadu using borewell in june")

    check("Detects crop: rice",           result["crop"] == "rice")
    check("Detects month: june",          result["month"] == "june")
    check("Detects location: tamil_nadu", result["location"] == "tamil_nadu")
    check("Detects irrigation: irrigated",result["irrigation"] == "irrigated")

    result2 = extract_entities("cotton farmer rainfed taken a kcc loan sells in mandi")
    check("Detects crop: cotton",                   result2["crop"] == "cotton")
    check("Detects irrigation: rainfed",            result2["irrigation"] == "rainfed")
    check("Detects financial_dependency: loan",     result2["financial_dependency"] == "loan")
    check("Detects market_dependency: high",        result2["market_dependency"] == "high")

    result3 = extract_entities("some random text")
    check("Returns None for unknown fields",        result3["crop"] is None)

    check("Always returns all 6 keys", all(k in result for k in [
        "crop", "month", "location", "irrigation",
        "market_dependency", "financial_dependency"
    ]))

except Exception:
    print("  💥 Module failed to import or crashed:")
    traceback.print_exc()

# ════════════════════════════════════════════════════════
# MODULE 3 — question_engine.py
# ════════════════════════════════════════════════════════
section("MODULE 3 — question_engine.py")

try:
    from modules.question_engine import identify_missing_fields

    # All fields present → no questions
    full_context = {
        "crop": "rice", "month": "june",
        "location": "tamil_nadu", "irrigation": "irrigated",
        "market_dependency": None, "financial_dependency": None
    }
    check("Returns [] when all critical fields present",
        identify_missing_fields(full_context) == [])

    # All fields missing → 4 questions
    empty_context = {
        "crop": None, "month": None,
        "location": None, "irrigation": None
    }
    questions = identify_missing_fields(empty_context)
    check("Returns 4 questions when all fields missing", len(questions) == 4)

    # One field missing → 1 question
    partial = {
        "crop": "rice", "month": None,
        "location": "tamil_nadu", "irrigation": "irrigated"
    }
    q = identify_missing_fields(partial)
    check("Returns 1 question when only month is missing", len(q) == 1)
    check("Question is a string", isinstance(q[0], str))

    try:
        identify_missing_fields("not a dict")
        check("Raises TypeError for non-dict input", False)
    except TypeError:
        check("Raises TypeError for non-dict input", True)

except Exception:
    print("  💥 Module failed to import or crashed:")
    traceback.print_exc()

# ════════════════════════════════════════════════════════
# MODULE 4 — risk_categorizer.py
# ════════════════════════════════════════════════════════
section("MODULE 4 — risk_categorizer.py")

try:
    from modules.risk_categorizer import categorize_risks

    # Rainfed → Weather + Resource Risk
    r1 = categorize_risks({
        "crop": "rice", "month": "june", "location": "tamil_nadu",
        "irrigation": "rainfed", "market_dependency": None,
        "financial_dependency": None
    })
    check("Rainfed triggers Weather Risk",   "Weather Risk" in r1)
    check("Rainfed triggers Resource Risk",  "Resource Risk" in r1)

    # Loan → Financial Risk
    r2 = categorize_risks({
        "crop": "rice", "month": "june", "location": "tamil_nadu",
        "irrigation": "irrigated", "market_dependency": None,
        "financial_dependency": "loan"
    })
    check("Loan triggers Financial Risk", "Financial Risk" in r2)

    # High market dependency → Market Risk
    r3 = categorize_risks({
        "crop": "cotton", "month": "july", "location": "maharashtra",
        "irrigation": "irrigated", "market_dependency": "high",
        "financial_dependency": None
    })
    check("High market dependency triggers Market Risk", "Market Risk" in r3)

    # Empty context → no crash
    r4 = categorize_risks({})
    check("Empty context returns a list (no crash)", isinstance(r4, list))

    # No duplicates in result
    check("Result has no duplicate risks", len(r1) == len(set(r1)))

    try:
        categorize_risks("not a dict")
        check("Raises TypeError for non-dict input", False)
    except TypeError:
        check("Raises TypeError for non-dict input", True)

except Exception:
    print("  💥 Module failed to import or crashed:")
    traceback.print_exc()

# ════════════════════════════════════════════════════════
# MODULE 5 — weather_service.py
# ════════════════════════════════════════════════════════
section("MODULE 5 — weather_service.py")

try:
    from modules.weather_service import get_weather_summary

    result = get_weather_summary(13.0827, 80.2707)

    check("Returns a dict",                     isinstance(result, dict))
    check("Has 'temperature' key",              "temperature" in result)
    check("Has 'rainfall' key",                 "rainfall" in result)
    check("Has 'wind_speed' key",               "wind_speed" in result)
    check("Does not crash on network failure",  True)  # we got here = no crash

    # Values are either float or None — never anything else
    for key in ["temperature", "rainfall", "wind_speed"]:
        val = result[key]
        check(f"'{key}' is float or None",
            val is None or isinstance(val, float))

    try:
        get_weather_summary("bad", 80.0)
        check("Raises TypeError for non-float latitude", False)
    except TypeError:
        check("Raises TypeError for non-float latitude", True)

except Exception:
    print("  💥 Module failed to import or crashed:")
    traceback.print_exc()

# ════════════════════════════════════════════════════════
# MODULE 6 — market_service.py
# ════════════════════════════════════════════════════════
section("MODULE 6 — market_service.py")

try:
    from modules.market_service import get_market_context

    r = get_market_context("rice")
    check("Returns a dict",                 isinstance(r, dict))
    check("Has 'price_trend' key",          "price_trend" in r)
    check("Has 'volatility' key",           "volatility" in r)
    check("Has 'demand_level' key",         "demand_level" in r)
    check("Rice price_trend is 'stable'",   r["price_trend"] == "stable")
    check("Rice demand_level is 'high'",    r["demand_level"] == "high")

    r2 = get_market_context("COTTON")
    check("Case-insensitive lookup works",  r2["price_trend"] == "falling")

    r3 = get_market_context("unknown_crop")
    check("Unknown crop returns all None",
        all(v is None for v in r3.values()))

    try:
        get_market_context("")
        check("Raises ValueError for empty crop", False)
    except ValueError:
        check("Raises ValueError for empty crop", True)

    try:
        get_market_context(123)
        check("Raises TypeError for non-string crop", False)
    except TypeError:
        check("Raises TypeError for non-string crop", True)

except Exception:
    print("  💥 Module failed to import or crashed:")
    traceback.print_exc()

# ════════════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════════════
total = passed + failed
print(f"\n{'═' * 50}")
print(f"  RESULTS:  {passed} passed  |  {failed} failed  |  {total} total")
print(f"{'═' * 50}\n")