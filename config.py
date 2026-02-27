"""
config.py — Mun-Echarikkai System Configuration

Central source of truth for all static configuration constants used across
the Mun-Echarikkai pipeline. Contains only immutable values — no business
logic, no functions, no classes, no environment variable handling.

All modules should import directly from this file.
"""

# ---------------------------------------------------------------------------
# LLM — Ollama local inference
# ---------------------------------------------------------------------------

OLLAMA_BASE_URL: str = "http://localhost:11434/api/generate"

OLLAMA_MODEL_NAME: str = "mistral"

# ---------------------------------------------------------------------------
# External APIs
# ---------------------------------------------------------------------------

WEATHER_API_BASE_URL: str = "https://api.open-meteo.com/v1/forecast"

# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

REQUEST_TIMEOUT: int = 60

# ---------------------------------------------------------------------------
# Input handling
# ---------------------------------------------------------------------------

SUPPORTED_INPUT_TYPES: list[str] = ["text"]