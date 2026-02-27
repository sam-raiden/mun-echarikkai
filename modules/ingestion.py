"""
modules/ingestion.py

Responsible for ingesting and normalizing raw input before further processing.
Supports only validated input types and performs no business logic.
"""

import re
import unicodedata


def normalize_input(input_type: str, input_data: str) -> str:
    """
    Normalize raw input data based on the specified input type.

    Performs the following normalization steps (for supported types):
        1. Validates that ``input_type`` is a supported type.
        2. Validates that ``input_data`` is a non-empty string.
        3. Applies Unicode NFC normalization (canonical decomposition, then
           canonical composition).
        4. Converts all characters to lowercase.
        5. Collapses any sequence of whitespace characters into a single space.
        6. Strips leading and trailing whitespace.

    Args:
        input_type (str): The type of input being provided. Currently only
            ``"text"`` is supported. Raises ``ValueError`` for any other value.
        input_data (str): The raw input string to normalize. Must be a
            non-empty string after stripping; raises ``ValueError`` otherwise.

    Returns:
        str: The fully normalized string.

    Raises:
        TypeError: If ``input_type`` or ``input_data`` is not a ``str``.
        ValueError: If ``input_type`` is not a supported type.
        ValueError: If ``input_data`` is empty or contains only whitespace.

    Examples:
        >>> normalize_input("text", "  Hello   World  ")
        'hello world'

        >>> normalize_input("text", "Héllo\\tWörld\\n")
        'héllo wörld'

        >>> normalize_input("image", "some data")
        ValueError: Unsupported input_type 'image'. Supported types: ['text']

        >>> normalize_input("text", "   ")
        ValueError: input_data must not be empty or whitespace-only.
    """
    _SUPPORTED_TYPES: list[str] = ["text"]

    # --- Type guards ---
    if not isinstance(input_type, str):
        raise TypeError(
            f"input_type must be a str, got {type(input_type).__name__!r}."
        )
    if not isinstance(input_data, str):
        raise TypeError(
            f"input_data must be a str, got {type(input_data).__name__!r}."
        )

    # --- Validate input_type ---
    if input_type not in _SUPPORTED_TYPES:
        raise ValueError(
            f"Unsupported input_type {input_type!r}. "
            f"Supported types: {_SUPPORTED_TYPES}"
        )


    # --- Validate input_data is not empty ---
    if not input_data.strip():
        raise ValueError("input_data must not be empty or whitespace-only.")

    # --- Normalize ---
    normalized: str = unicodedata.normalize("NFC", input_data)
    normalized = normalized.lower()
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = normalized.strip()

    return normalized