"""
modules/market_service.py

Responsible for loading and returning crop-level market context from a local
knowledge base (data/crop_knowledge.json).

No external API calls, no LLM inference, no risk scoring, no business logic
beyond data retrieval and safe field extraction.
"""

import json
import os
from typing import Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Path is resolved relative to this file so the module works regardless of
# the working directory from which the application is launched.
_DEFAULT_DATA_PATH: str = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "data",
    "crop_knowledge.json",
)

_VALID_PRICE_TRENDS: frozenset[str] = frozenset({"rising", "stable", "falling"})
_VALID_VOLATILITIES: frozenset[str] = frozenset({"high", "medium", "low"})
_VALID_DEMAND_LEVELS: frozenset[str] = frozenset({"high", "medium", "low"})


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_crop_db(data_path: str) -> dict:
    """
    Load and parse the crop knowledge JSON file from ``data_path``.

    Args:
        data_path (str): Absolute or relative path to ``crop_knowledge.json``.

    Returns:
        dict: The parsed JSON object. Returns an empty dict on any I/O or
            parse failure so callers always receive a safe value.
    """
    try:
        with open(data_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}
    except OSError:
        return {}


def _safe_field(
    value: object,
    allowed: frozenset[str],
) -> Optional[str]:
    """
    Return ``value`` as a lowercase string if it belongs to ``allowed``,
    otherwise return ``None``.

    Prevents unexpected or corrupted values in the JSON from leaking into
    downstream modules.

    Args:
        value (object): Raw value read from the crop record.
        allowed (frozenset[str]): Set of valid canonical string values.

    Returns:
        Optional[str]: The validated lowercase string, or ``None``.
    """
    if not isinstance(value, str):
        return None
    normalized: str = value.strip().lower()
    return normalized if normalized in allowed else None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_market_context(
    crop: str,
    *,
    data_path: str = _DEFAULT_DATA_PATH,
) -> dict:
    """
    Return a structured market context summary for the specified crop by
    reading from the local ``data/crop_knowledge.json`` knowledge base.

    The function is stateless: the JSON file is loaded fresh on every call
    (suitable for a prototype; a caching layer can be added externally if
    performance requires it without modifying this module).

    Fields returned
    ---------------
    price_trend
        Direction of recent price movement: ``"rising"``, ``"stable"``, or
        ``"falling"``. ``None`` if the crop is unknown or the field is absent
        / invalid in the knowledge base.
    volatility
        Price volatility classification: ``"high"``, ``"medium"``, or
        ``"low"``. ``None`` under the same conditions.
    demand_level
        Current market demand level: ``"high"``, ``"medium"``, or ``"low"``.
        ``None`` under the same conditions.

    Args:
        crop (str): The canonical crop name to look up (e.g. ``"rice"``,
            ``"cotton"``). Case-insensitive; leading/trailing whitespace is
            stripped before lookup. Must be a non-empty string.
        data_path (str, optional): Path to the crop knowledge JSON file.
            Defaults to ``data/crop_knowledge.json`` relative to the project
            root. Exposed as a keyword-only argument to support testing with
            fixture files without modifying module-level state.

    Returns:
        dict: A dictionary with exactly these keys:
            ``"price_trend"`` (``str | None``),
            ``"volatility"`` (``str | None``),
            ``"demand_level"`` (``str | None``).
            All values are ``None`` if the crop is not found, the data file
            is missing, or a field value fails validation.

    Raises:
        TypeError: If ``crop`` is not a ``str``.
        ValueError: If ``crop`` is empty or whitespace-only.

    Examples:
        >>> get_market_context("rice")
        {'price_trend': 'stable', 'volatility': 'low', 'demand_level': 'high'}

        >>> get_market_context("cotton")
        {'price_trend': 'falling', 'volatility': 'high', 'demand_level': 'medium'}

        >>> get_market_context("unknown_crop")
        {'price_trend': None, 'volatility': None, 'demand_level': None}
    """
    # --- Type and value guards ---
    if not isinstance(crop, str):
        raise TypeError(
            f"crop must be a str, got {type(crop).__name__!r}."
        )
    if not crop.strip():
        raise ValueError("crop must not be empty or whitespace-only.")

    _empty: dict[str, Optional[str]] = {
        "price_trend": None,
        "volatility": None,
        "demand_level": None,
    }

    # --- Load knowledge base ---
    db: dict = _load_crop_db(data_path)
    if not db:
        return _empty.copy()

    # --- Locate crop record ---
    crops_section: dict = db.get("crops", {})
    if not isinstance(crops_section, dict):
        return _empty.copy()

    crop_key: str = crop.strip().lower()
    record: Optional[dict] = crops_section.get(crop_key)

    if not isinstance(record, dict):
        return _empty.copy()

    # --- Extract and validate each field ---
    return {
        "price_trend": _safe_field(record.get("price_trend"), _VALID_PRICE_TRENDS),
        "volatility": _safe_field(record.get("volatility"), _VALID_VOLATILITIES),
        "demand_level": _safe_field(record.get("demand_level"), _VALID_DEMAND_LEVELS),
    }


# ---------------------------------------------------------------------------
# Manual smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_crops = ["rice", "cotton", "onion", "tomato", "WHEAT", "unknown_crop", ""]

    for c in test_crops:
        try:
            result = get_market_context(c)
            print(f"{c!r:20s} → {result}")
        except ValueError as exc:
            print(f"{c!r:20s} → ValueError: {exc}")
        except TypeError as exc:
            print(f"{c!r:20s} → TypeError: {exc}")