"""
modules/formatter.py

Responsible for parsing raw LLM text output into a structured dictionary.
Uses safe line-by-line string parsing only — no eval, no complex regex,
no business logic, no scoring adjustments.

If any section is missing or malformed, returns safe defaults.
Never crashes on unexpected input.
"""

from typing import Optional


# ---------------------------------------------------------------------------
# Constants — section header markers exactly as enforced by prompt_builder
# ---------------------------------------------------------------------------

_SECTION_HEADERS: tuple[str, ...] = (
    "HIGH_RISKS:",
    "MEDIUM_RISKS:",
    "ASSUMPTIONS:",
    "MITIGATION:",
    "RISK_SCORE:",
    "CONFIDENCE_LEVEL:",
)

_VALID_CONFIDENCE_LEVELS: frozenset[str] = frozenset({"low", "medium", "high"})


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_sections(response: str) -> dict[str, list[str]]:
    """
    Split the raw LLM response into named sections by detecting header lines.

    Each section begins at its header and ends at the next header or end of
    string. Lines are collected as-is for further parsing by the caller.

    Args:
        response (str): Raw LLM response string.

    Returns:
        dict[str, list[str]]: Mapping of header string → list of raw lines
            that follow it (excluding the header line itself).
    """
    sections: dict[str, list[str]] = {}
    current_header: Optional[str] = None

    for raw_line in response.splitlines():
        line: str = raw_line.strip()

        # Check if this line is a known section header.
        matched_header: Optional[str] = None
        for header in _SECTION_HEADERS:
            if line.startswith(header):
                matched_header = header
                break

        if matched_header is not None:
            current_header = matched_header
            # For inline headers like "RISK_SCORE: 7", capture remainder now.
            remainder: str = line[len(matched_header):].strip()
            sections.setdefault(current_header, [])
            if remainder:
                sections[current_header].append(remainder)
        elif current_header is not None:
            sections[current_header].append(line)

    return sections


def _parse_bullet_lines(lines: list[str]) -> list[str]:
    """
    Extract non-empty bullet items from a list of raw section lines.

    Accepts lines starting with ``*``, ``-``, or ``•``. Lines that are
    empty, equal to ``"None"``, or contain only punctuation are discarded.

    Args:
        lines (list[str]): Raw lines collected under a section header.

    Returns:
        list[str]: Cleaned list of item strings with bullet prefix removed.
    """
    items: list[str] = []
    for line in lines:
        stripped: str = line.strip()
        if not stripped:
            continue
        # Remove bullet prefix if present.
        if stripped.startswith(("* ", "- ", "• ")):
            content: str = stripped[2:].strip()
        elif stripped.startswith(("*", "-", "•")):
            content = stripped[1:].strip()
        else:
            content = stripped

        # Discard placeholder values.
        if not content or content.lower() in {"none", "-", "n/a"}:
            continue

        items.append(content)
    return items


def _parse_risk_score(lines: list[str]) -> Optional[int]:
    """
    Extract a valid integer risk score (1–10) from section lines.

    Args:
        lines (list[str]): Lines collected under the ``RISK_SCORE:`` header.

    Returns:
        Optional[int]: Integer score between 1 and 10, or ``None`` if not
            found or out of range.
    """
    for line in lines:
        token: str = line.strip()
        # Handle "RISK_SCORE: 7" inline or just "7" on its own line.
        if ":" in token:
            token = token.split(":", 1)[-1].strip()
        # Extract leading digits only.
        digits: str = ""
        for ch in token:
            if ch.isdigit():
                digits += ch
            elif digits:
                break
        if digits:
            try:
                score: int = int(digits)
                if 1 <= score <= 10:
                    return score
            except ValueError:
                continue
    return None


def _parse_confidence_level(lines: list[str]) -> Optional[str]:
    """
    Extract a valid confidence level string from section lines.

    Args:
        lines (list[str]): Lines collected under the ``CONFIDENCE_LEVEL:``
            header.

    Returns:
        Optional[str]: One of ``"low"``, ``"medium"``, or ``"high"``, or
            ``None`` if not found or invalid.
    """
    for line in lines:
        token: str = line.strip().lower()
        if ":" in token:
            token = token.split(":", 1)[-1].strip()
        # Accept the first word if it matches a valid level.
        word: str = token.split()[0] if token.split() else ""
        if word in _VALID_CONFIDENCE_LEVELS:
            return word
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_llm_response(response: str) -> dict:
    """
    Parse a raw LLM response string into a structured dictionary with typed
    fields.

    Expects the LLM to have followed the output format enforced by
    ``prompt_builder.build_prompt``::

        HIGH_RISKS:
        * ...

        MEDIUM_RISKS:
        * ...

        ASSUMPTIONS:
        * ...

        MITIGATION:
        * ...

        RISK_SCORE: <1-10>
        CONFIDENCE_LEVEL: <low|medium|high>

    The parser is lenient by design — it never raises on malformed output.
    Missing sections return empty lists or ``None``. Extra text, blank lines,
    and minor formatting deviations are silently handled.

    Args:
        response (str): Raw LLM output string, typically the return value of
            ``llm_service.call_llm``. Must be a ``str``; may be empty.

    Returns:
        dict: A dictionary with exactly these keys:

            - ``"high_risks"``       (``list[str]``) — high severity risks
            - ``"medium_risks"``     (``list[str]``) — medium severity risks
            - ``"assumptions"``      (``list[str]``) — assumptions made
            - ``"mitigation"``       (``list[str]``) — mitigation steps
            - ``"risk_score"``       (``int | None``) — score from 1 to 10
            - ``"confidence_level"`` (``str | None``) — low, medium, or high

    Raises:
        TypeError: If ``response`` is not a ``str``.

    Examples:
        >>> raw = \"\"\"
        ... HIGH_RISKS:
        ... * Drought risk due to rainfed irrigation
        ... MEDIUM_RISKS:
        ... * Price volatility for cotton
        ... ASSUMPTIONS:
        ... * Normal monsoon assumed
        ... MITIGATION:
        ... * Install drip irrigation
        ... RISK_SCORE: 7
        ... CONFIDENCE_LEVEL: medium
        ... \"\"\"
        >>> result = parse_llm_response(raw)
        >>> result["risk_score"]
        7
        >>> result["confidence_level"]
        'medium'
        >>> result["high_risks"]
        ['Drought risk due to rainfed irrigation']
    """
    if not isinstance(response, str):
        raise TypeError(
            f"response must be a str, got {type(response).__name__!r}."
        )

    _empty: dict = {
        "high_risks": [],
        "medium_risks": [],
        "assumptions": [],
        "mitigation": [],
        "risk_score": None,
        "confidence_level": None,
    }

    if not response.strip():
        return _empty.copy()

    sections: dict[str, list[str]] = _extract_sections(response)

    return {
        "high_risks":       _parse_bullet_lines(sections.get("HIGH_RISKS:", [])),
        "medium_risks":     _parse_bullet_lines(sections.get("MEDIUM_RISKS:", [])),
        "assumptions":      _parse_bullet_lines(sections.get("ASSUMPTIONS:", [])),
        "mitigation":       _parse_bullet_lines(sections.get("MITIGATION:", [])),
        "risk_score":       _parse_risk_score(sections.get("RISK_SCORE:", [])),
        "confidence_level": _parse_confidence_level(sections.get("CONFIDENCE_LEVEL:", [])),
    }


# ---------------------------------------------------------------------------
# Manual smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    sample = """
HIGH_RISKS:
* Drought risk due to rainfed irrigation during low-rainfall month
* KCC loan repayment pressure if harvest fails

MEDIUM_RISKS:
* Price volatility for rice in local mandi
* Temperature exceeding optimal range for grain filling

ASSUMPTIONS:
* Normal monsoon conditions assumed for June
* No pest outbreak assumed

MITIGATION:
* Adopt drip irrigation to reduce water dependency
* Explore crop insurance schemes such as PMFBY
* Diversify into short-duration pulses as contingency

RISK_SCORE: 7
CONFIDENCE_LEVEL: medium
"""

    result = parse_llm_response(sample)
    print(json.dumps(result, indent=2))

    # Edge case — completely empty response
    print("\nEmpty input:")
    print(json.dumps(parse_llm_response(""), indent=2))

    # Edge case — fallback response from llm_service
    fallback = """HIGH_RISKS:
* None

MEDIUM_RISKS:
* None

ASSUMPTIONS:
* LLM unavailable

MITIGATION:
* Manual review required

RISK_SCORE: 5
CONFIDENCE_LEVEL: low"""

    print("\nFallback input:")
    print(json.dumps(parse_llm_response(fallback), indent=2))