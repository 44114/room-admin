"""
Internationalization (i18n) module for the Admin Panel.

Provides:
- JSON-based translation files loaded from static/lang/
- Browser language detection via Accept-Language header
- Session/query-param language override
- Jinja2 context processor injecting `_()` and `current_lang`
"""

import json
import logging
import os

from flask import session, request, g

logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────────
TRANSLATIONS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "static", "lang"
)

FALLBACK_LANG = "en"

SUPPORTED_LANGUAGES: dict[str, str] = {
    "en": "English",
    "zh-CN": "简体中文",
    "zh-TW": "繁體中文",
    "ja": "日本語",
    "ko": "한국어",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "pt": "Português",
    "ru": "Русский",
    "vi": "Tiếng Việt",
    "th": "ไทย",
}

# Cache loaded translations
_translations_cache: dict[str, dict[str, str]] = {}
_loaded: set[str] = set()
_i18n_initialized = False


# ── Translation loading ─────────────────────────────────────────────

def _load_translations(lang: str) -> dict[str, str]:
    """Load translation dictionary for *lang* from disk (cached)."""
    if lang in _loaded:
        return _translations_cache.get(lang, {})

    filepath = os.path.join(TRANSLATIONS_DIR, f"{lang}.json")
    try:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.warning("Translation file not found: %s", filepath)
        data = {}
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in %s: %s", filepath, e)
        data = {}

    _translations_cache[lang] = data
    _loaded.add(lang)
    return data


def _flatten_translations(data: dict, prefix: str = "") -> dict[str, str]:
    """Flatten nested dict into dot-separated key→string mapping."""
    result: dict[str, str] = {}
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            result.update(_flatten_translations(value, full_key))
        elif isinstance(value, str):
            result[full_key] = value
    return result


# ── Language detection ──────────────────────────────────────────────

def _parse_accept_language(header: str) -> list[str]:
    """Parse Accept-Language header, returning languages in priority order."""
    if not header:
        return []
    languages = []
    for part in header.split(","):
        part = part.strip()
        if not part:
            continue
        lang = part.split(";")[0].strip()
        if lang:
            languages.append(lang)
    return languages


def _normalize_lang(lang: str) -> str:
    """Normalize a language tag to one of our supported codes."""
    if lang in SUPPORTED_LANGUAGES:
        return lang
    lang_lower = lang.lower()
    for code in SUPPORTED_LANGUAGES:
        if code.lower() == lang_lower:
            return code
    primary = lang.split("-")[0].lower() if "-" in lang else lang_lower
    if primary == "zh":
        return "zh-CN"
    for code in SUPPORTED_LANGUAGES:
        if code.lower().startswith(primary):
            return code
    return lang


def detect_language() -> str:
    """Detect the user's preferred language.

    Priority: query param `lang` > session `lang` > Accept-Language header > fallback.
    """
    lang_param = request.args.get("lang", "")
    if lang_param and lang_param in SUPPORTED_LANGUAGES:
        session["lang"] = lang_param
        session.modified = True
        return lang_param

    session_lang = session.get("lang", "")
    if session_lang in SUPPORTED_LANGUAGES:
        return session_lang

    accept = request.headers.get("Accept-Language", "")
    for lang in _parse_accept_language(accept):
        normalized = _normalize_lang(lang)
        if normalized in SUPPORTED_LANGUAGES:
            session.setdefault("lang", normalized)
            return normalized

    return FALLBACK_LANG


# ── Translation function ────────────────────────────────────────────

class Translations:
    """Holds translations for a detected language, with fallback to English."""

    def __init__(self, lang: str):
        self.lang = lang
        self._translations = _flatten_translations(_load_translations(lang))
        self._fallback = {}
        if lang != FALLBACK_LANG:
            self._fallback = _flatten_translations(_load_translations(FALLBACK_LANG))

    def get(self, key: str) -> str:
        """Translate *key* to the current language, falling back to English."""
        val = self._translations.get(key)
        if val is not None:
            return val
        val = self._fallback.get(key)
        if val is not None:
            return val
        return key


def _trans(key: str) -> str:
    """Translation function for both Python code and Jinja2 templates.

    In templates:  {{ _('nav.dashboard') }}
    In Python:     from i18n import _;  _('nav.dashboard')
    """
    translations: Translations | None = g.get("_translations")
    if translations is None:
        return key
    return translations.get(key)


# Module-level alias for Python code:  from i18n import _
_ = _trans


# ── Flask integration ───────────────────────────────────────────────

def init_i18n(app):
    """Register i18n-related hooks and context processors with the Flask app."""
    global _i18n_initialized
    if _i18n_initialized:
        return
    _i18n_initialized = True

    @app.before_request
    def _set_language():
        """Detect language and attach Translations to g before every request."""
        lang = detect_language()
        g.current_lang = lang
        g._translations = Translations(lang)

    @app.context_processor
    def _inject_i18n():
        """Inject i18n helpers into all templates."""
        return {
            "_": _trans,
            "current_lang": getattr(g, "current_lang", FALLBACK_LANG),
            "supported_languages": SUPPORTED_LANGUAGES,
        }

    @app.route("/lang/<lang>")
    def set_language(lang):
        """Endpoint to change language manually. Redirects back."""
        if lang in SUPPORTED_LANGUAGES:
            session["lang"] = lang
            session.modified = True
        next_url = request.args.get("next", "/")
        from flask import redirect
        return redirect(next_url)

    logger.info("i18n initialized with %d languages", len(SUPPORTED_LANGUAGES))
