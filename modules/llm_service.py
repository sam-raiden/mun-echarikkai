"""
modules/llm_service.py

Responsible for sending a constructed prompt to a locally running Ollama
LLM instance and returning the raw text response.

No response parsing. No business logic. No scoring. Graceful fallback on
any failure. Reads all connection settings from config.py.
"""

import requests

from config import OLLAMA_BASE_URL, OLLAMA_MODEL_NAME, REQUEST_TIMEOUT


# ---------------------------------------------------------------------------
# Fallback constant
# ---------------------------------------------------------------------------

_FALLBACK_RESPONSE: str = """HIGH_RISKS:
* None

MEDIUM_RISKS:
* None

ASSUMPTIONS:
* LLM unavailable

MITIGATION:
* Manual review required

RISK_SCORE: 5
CONFIDENCE_LEVEL: low"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def call_llm(prompt: str) -> str:
    """
    Send a prompt string to the locally running Ollama LLM and return the
    raw text response exactly as received.

    The function reads connection configuration from ``config.py``:
        - ``OLLAMA_BASE_URL``   — base URL of the Ollama server
          (e.g. ``"http://localhost:11434"``)
        - ``OLLAMA_MODEL_NAME`` — name of the model to invoke
          (e.g. ``"mistral"``)
        - ``REQUEST_TIMEOUT``  — HTTP request timeout in seconds

    The POST body sent to Ollama is::

        {
            "model":  <OLLAMA_MODEL_NAME>,
            "prompt": <prompt>,
            "stream": false
        }

    On any failure — network error, timeout, HTTP error, or malformed
    response — the function does **not** raise an exception. Instead it
    returns a structured fallback string in the exact required output format
    so downstream parsing is never broken.

    Fallback response returned on failure::

        HIGH_RISKS:
        * None

        MEDIUM_RISKS:
        * None

        ASSUMPTIONS:
        * LLM unavailable

        MITIGATION:
        * Manual review required

        RISK_SCORE: 5
        CONFIDENCE_LEVEL: low

    Args:
        prompt (str): The fully constructed prompt string, typically produced
            by ``prompt_builder.build_prompt``. Must be a non-empty string.

    Returns:
        str: The raw LLM response text as returned by Ollama, or the
            structured fallback string if the call fails for any reason.
            The response is never parsed or modified.

    Raises:
        TypeError: If ``prompt`` is not a ``str``.
        ValueError: If ``prompt`` is empty or whitespace-only.

    Examples:
        >>> response = call_llm("Analyze this farm profile...")
        >>> isinstance(response, str)
        True
        >>> response.startswith("HIGH_RISKS:") or "LLM unavailable" in response
        True
    """
    # --- Type guards ---
    if not isinstance(prompt, str):
        raise TypeError(
            f"prompt must be a str, got {type(prompt).__name__!r}."
        )
    if not prompt.strip():
        raise ValueError("prompt must not be empty or whitespace-only.")

    url: str = OLLAMA_BASE_URL

    payload: dict = {
        "model": OLLAMA_MODEL_NAME,
        "prompt": prompt,
        "stream": False,
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code != 200:
            return _FALLBACK_RESPONSE

        json_response: dict = response.json()
        raw_text: str = json_response["response"]

        if not isinstance(raw_text, str) or not raw_text.strip():
            return _FALLBACK_RESPONSE

        return raw_text

    except Exception:
        return _FALLBACK_RESPONSE


# ---------------------------------------------------------------------------
# Manual smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_prompt = (
        "HIGH_RISKS:\n* Test prompt — Ollama may not be running.\n"
        "RISK_SCORE: 1\nCONFIDENCE_LEVEL: low"
    )

    print(f"Sending prompt to: {OLLAMA_BASE_URL}")
    print(f"Model            : {OLLAMA_MODEL_NAME}")
    print(f"Timeout          : {REQUEST_TIMEOUT}s\n")

    result = call_llm(test_prompt)
    print("── LLM Response ──────────────────────────────")
    print(result)
    print("──────────────────────────────────────────────")