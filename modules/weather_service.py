"""
modules/weather_service.py

Responsible for fetching current weather conditions from the Open-Meteo
public API for a given geographic coordinate.

No risk scoring, no business logic, no LLM calls, no external dependencies
beyond the standard `requests` library.
"""

import requests
from typing import Optional


_OPEN_METEO_URL: str = "https://api.open-meteo.com/v1/forecast"
_CURRENT_VARIABLES: str = "temperature_2m,rain,wind_speed_10m"
_REQUEST_TIMEOUT_SECONDS: int = 10


def get_weather_summary(latitude: float, longitude: float) -> dict:
    """Fetch current weather summary for given coordinates."""
    if not isinstance(latitude, (int, float)):
        raise TypeError(f"latitude must be a float, got {type(latitude).__name__!r}.")
    if not isinstance(longitude, (int, float)):
        raise TypeError(f"longitude must be a float, got {type(longitude).__name__!r}.")

    _empty: dict[str, Optional[float]] = {
        "temperature": None,
        "rainfall": None,
        "wind_speed": None,
    }

    params: dict = {
        "latitude": latitude,
        "longitude": longitude,
        "current": _CURRENT_VARIABLES,
        "timezone": "auto",
    }

    try:
        response = requests.get(_OPEN_METEO_URL, params=params, timeout=_REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload: dict = response.json()
    except requests.exceptions.Timeout:
        return _empty.copy()
    except requests.exceptions.ConnectionError:
        return _empty.copy()
    except requests.exceptions.HTTPError:
        return _empty.copy()
    except requests.exceptions.RequestException:
        return _empty.copy()
    except ValueError:
        return _empty.copy()

    try:
        current: dict = payload["current"]
        temperature: Optional[float] = _to_float(current.get("temperature_2m"))
        rainfall: Optional[float] = _to_float(current.get("rain"))
        wind_speed: Optional[float] = _to_float(current.get("wind_speed_10m"))
    except (KeyError, TypeError):
        return _empty.copy()

    return {
        "temperature": temperature,
        "rainfall": rainfall,
        "wind_speed": wind_speed,
    }


def _to_float(value: object) -> Optional[float]:
    """Safely coerce a value to float, returning None on failure."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None