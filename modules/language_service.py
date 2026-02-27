"""
modules/language_service.py

Responsible for language detection and translation services within the
Mun-Echarikkai pipeline.

Prototype implementation uses rule-based Unicode range detection and
placeholder translations. The module is architected for clean replacement
with AWS Translate (or any other translation backend) by swapping only
the internal implementation of each function — all public signatures and
return contracts remain stable.

No external API calls in this version. No AWS integration. No LLM calls.
"""


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Tamil Unicode block: U+0B80 to U+0BFF
_TAMIL_UNICODE_START: int = 0x0B80
_TAMIL_UNICODE_END: int   = 0x0BFF

_LANG_ENGLISH: str = "en"
_LANG_TAMIL: str   = "ta"

_SUPPORTED_LANGUAGES: frozenset[str] = frozenset({_LANG_ENGLISH, _LANG_TAMIL})

# Placeholder messages — replace with real translations in production.
_PLACEHOLDER_TO_ENGLISH: str = (
    "[Tamil text detected — translation not implemented in prototype]"
)
_PLACEHOLDER_TO_TAMIL: str = (
    "[Tamil translation not implemented in prototype]"
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _contains_tamil(text: str) -> bool:
    """
    Return True if any character in ``text`` falls within the Tamil Unicode
    block (U+0B80 – U+0BFF).

    Args:
        text (str): Input string to inspect.

    Returns:
        bool: ``True`` if at least one Tamil Unicode character is found.
    """
    return any(_TAMIL_UNICODE_START <= ord(ch) <= _TAMIL_UNICODE_END for ch in text)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_language(text: str) -> str:
    """
    Detect the primary language of the input text using Unicode range analysis.

    Prototype detection logic
    -------------------------
    - If any character in ``text`` falls within the Tamil Unicode block
      (U+0B80 – U+0BFF) → returns ``"ta"``
    - Otherwise → returns ``"en"``

    This function is designed to be replaced with a call to AWS Comprehend
    or AWS Translate's ``detect_dominant_language`` API in production without
    changing its signature or return contract.

    Args:
        text (str): The input string to analyse. Must be a non-empty string.

    Returns:
        str: ISO 639-1 language code. ``"ta"`` for Tamil, ``"en"`` for all
            other input in this prototype.

    Raises:
        TypeError: If ``text`` is not a ``str``.
        ValueError: If ``text`` is empty or whitespace-only.

    Examples:
        >>> detect_language("Hello world")
        'en'

        >>> detect_language("வணக்கம்")   # Tamil for "Hello"
        'ta'

        >>> detect_language("I grow rice in Tamil Nadu")
        'en'
    """
    if not isinstance(text, str):
        raise TypeError(
            f"text must be a str, got {type(text).__name__!r}."
        )
    if not text.strip():
        raise ValueError("text must not be empty or whitespace-only.")

    if _contains_tamil(text):
        return _LANG_TAMIL

    return _LANG_ENGLISH


def translate_to_english(text: str) -> str:
    """
    Translate input text to English.

    If the detected language is already English, the original text is
    returned unchanged. For Tamil input, a placeholder string is returned
    in this prototype — replace the body with an AWS Translate API call
    for production use.

    Args:
        text (str): The input string to translate. Must be a non-empty string.

    Returns:
        str: The English text, or a placeholder string if translation is not
            yet implemented for the detected language.

    Raises:
        TypeError: If ``text`` is not a ``str``.
        ValueError: If ``text`` is empty or whitespace-only.

    Examples:
        >>> translate_to_english("I grow rice in Tamil Nadu")
        'I grow rice in Tamil Nadu'

        >>> translate_to_english("வணக்கம்")
        '[Tamil text detected — translation not implemented in prototype]'
    """
    if not isinstance(text, str):
        raise TypeError(
            f"text must be a str, got {type(text).__name__!r}."
        )
    if not text.strip():
        raise ValueError("text must not be empty or whitespace-only.")

    detected: str = detect_language(text)

    if detected == _LANG_ENGLISH:
        return text

    if detected == _LANG_TAMIL:
        # TODO: Replace with AWS Translate call:
        # import boto3
        # client = boto3.client("translate", region_name="ap-south-1")
        # result = client.translate_text(
        #     Text=text, SourceLanguageCode="ta", TargetLanguageCode="en"
        # )
        # return result["TranslatedText"]
        return _PLACEHOLDER_TO_ENGLISH

    # Fallback for any future language additions not yet handled.
    return text


def translate_from_english(text: str, target_lang: str) -> str:
    """
    Translate English text into the specified target language.

    If the target language is English, the original text is returned
    unchanged. For Tamil, a placeholder string is returned in this
    prototype — replace the body with an AWS Translate API call for
    production use.

    Args:
        text (str): The English source string to translate. Must be a
            non-empty string.
        target_lang (str): ISO 639-1 language code for the target language.
            Supported values in this prototype: ``"en"``, ``"ta"``.
            Unsupported codes return the original text unchanged.

    Returns:
        str: The translated text in ``target_lang``, or a placeholder string
            if translation is not yet implemented for that language, or the
            original text if ``target_lang`` is ``"en"`` or unsupported.

    Raises:
        TypeError: If ``text`` or ``target_lang`` is not a ``str``.
        ValueError: If ``text`` is empty or whitespace-only.
        ValueError: If ``target_lang`` is empty or whitespace-only.

    Examples:
        >>> translate_from_english("Your crop risk is high.", "en")
        'Your crop risk is high.'

        >>> translate_from_english("Your crop risk is high.", "ta")
        '[Tamil translation not implemented in prototype]'

        >>> translate_from_english("Your crop risk is high.", "hi")
        'Your crop risk is high.'
    """
    if not isinstance(text, str):
        raise TypeError(
            f"text must be a str, got {type(text).__name__!r}."
        )
    if not isinstance(target_lang, str):
        raise TypeError(
            f"target_lang must be a str, got {type(target_lang).__name__!r}."
        )
    if not text.strip():
        raise ValueError("text must not be empty or whitespace-only.")
    if not target_lang.strip():
        raise ValueError("target_lang must not be empty or whitespace-only.")

    lang: str = target_lang.strip().lower()

    if lang == _LANG_ENGLISH:
        return text

    if lang == _LANG_TAMIL:
        # TODO: Replace with AWS Translate call:
        # import boto3
        # client = boto3.client("translate", region_name="ap-south-1")
        # result = client.translate_text(
        #     Text=text, SourceLanguageCode="en", TargetLanguageCode="ta"
        # )
        # return result["TranslatedText"]
        return _PLACEHOLDER_TO_TAMIL

    # Unsupported target language — return original text unchanged.
    return text


# ---------------------------------------------------------------------------
# Manual smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("── detect_language ───────────────────────────────────")
    print(detect_language("Hello world"))                     # en
    print(detect_language("I grow rice in Tamil Nadu"))       # en
    print(detect_language("வணக்கம்"))                         # ta
    print(detect_language("நான் நெல் விவசாயம் செய்கிறேன்"))  # ta

    print("\n── translate_to_english ──────────────────────────────")
    print(translate_to_english("I grow rice in Tamil Nadu"))  # unchanged
    print(translate_to_english("வணக்கம்"))                    # placeholder

    print("\n── translate_from_english ────────────────────────────")
    print(translate_from_english("Your crop risk is high.", "en"))  # unchanged
    print(translate_from_english("Your crop risk is high.", "ta"))  # placeholder
    print(translate_from_english("Your crop risk is high.", "hi"))  # unchanged (unsupported)
    