"""
SpinRender Locale Loader — YAML-based localization system.

This module provides the Locale singleton that loads localized content (labels, icons)
from YAML configuration. YAML loading is strictly required.
"""
import logging
from pathlib import Path
from typing import Any

# Try to import PyYAML
_yaml_available = False
try:
    import yaml
    _yaml_available = True
except ImportError:
    yaml = None

logger = logging.getLogger("SpinRender")


class Locale:
    """Singleton locale manager with dot-path lookup.

    Usage:
        Locale.load("en_US")           # Load locale by language, sets singleton
        Locale.current()               # Get loaded singleton
        Locale.current().get("component.button.render.label")  # → "RENDER"
    """
    _instance: "Locale | None" = None
    _data: dict[str, Any] = {}
    _loaded_mtime: float = 0
    _loaded_name: str = ""

    def __init__(self, data: dict):
        self._data = data

    @classmethod
    def load(cls, name: str = "en_US") -> "Locale":
        """Load locale from YAML file. Sets singleton instance."""
        # Resolve path: resources/locale/{name}.yaml
        path = (Path(__file__).parent.parent / "resources" / "locale" / f"{name}.yaml").resolve()

        if not path.exists():
            error_msg = f"Locale file not found: {path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        # Check mtime to auto-detect disk changes
        mtime = path.stat().st_mtime
        is_stale = mtime > cls._loaded_mtime or name != cls._loaded_name

        # Idempotent: if already loaded and not forcing/stale, return existing instance
        if cls._instance is not None and not is_stale:
            return cls._instance

        logger.info(f"Locale: {'Reloading' if is_stale else 'Initializing'} '{name}' locale loading.")

        if not _yaml_available:
            error_msg = "PyYAML is not available. Locale system requires PyYAML."
            logger.error(error_msg)
            raise ImportError(error_msg)

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            # Extract the language-specific subtree: data["locale"][name]
            if "locale" not in data:
                raise RuntimeError(f"Locale YAML missing top-level 'locale' key")
            if name not in data["locale"]:
                raise RuntimeError(f"Locale '{name}' not defined in YAML (expected under 'locale.{name}')")
            locale_data = data["locale"][name]

            # Print full loaded locale data at INFO level (like Theme)
            debug_data = yaml.dump(locale_data, sort_keys=False, default_flow_style=False)
            logger.info(f"Locale Data (Loaded from {path.name}):\n{debug_data}")

            if cls._instance:
                # Update existing instance's data dictionary in-place
                cls._instance._data = locale_data
            else:
                cls._instance = cls(locale_data)

            cls._loaded_mtime = mtime
            cls._loaded_name = name
            logger.info(f"Locale: '{name}' locale loaded successfully.")
        except Exception as e:
            error_msg = f"Failed to parse locale '{name}' from {path}: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        return cls._instance

    @classmethod
    def reload(cls) -> "Locale":
        """Force a reload of the current locale from disk."""
        name = cls._loaded_name if cls._loaded_name else "en_US"
        # load() already handles extraction, just call it
        instance = cls.load(name=name)

        if _yaml_available:
            try:
                debug_data = yaml.dump(instance._data, sort_keys=False, default_flow_style=False)
                logger.info(f"Locale Data (Reloaded):\n{debug_data}")
            except Exception as e:
                logger.info(f"Locale Data (Reloaded - Raw): {instance._data}")
                logger.error(f"Failed to dump locale debug data: {e}")
        else:
            logger.info(f"Locale Data (Reloaded - Raw): {instance._data}")

        return instance

    @classmethod
    def current(cls) -> "Locale":
        """Get the current locale singleton, loading default if not set."""
        if cls._instance is None:
            cls.load()
        return cls._instance

    def get(self, key: str, default: Any = None) -> Any:
        """Get a localized value by dot-path key.

        Supports flattened dot-notation keys (e.g., "component.main.header.title").
        Uses longest-prefix matching: tries full key first, then progressively
        shorter prefixes to find a dot-composed key at any level.

        Example:
            locale.get("component.button.render.label") → "RENDER"
            locale.get("component.button.render.icon_ref") → "glyphs.render-action"
            locale.get("parameters.board_tilt.unit") → "°"

        Returns:
            The value at the key path, or `default` if key not found.
            If key not found and default is None, returns None.
        """
        keys = key.split('.')
        n = len(keys)

        # Try longest prefix matching: i = number of prefix segments to match as a single top-level/flattened key
        # Then remainder segments are traversed inside that sub-dict
        for i in range(n, 0, -1):
            prefix = '.'.join(keys[:i])
            if prefix in self._data:
                current = self._data[prefix]
                remainder = keys[i:]

                # Traverse remaining segments normally inside the sub-dict
                for k in remainder:
                    if not isinstance(current, dict):
                        logger.debug(f"Locale: Traversal stopped at non-dict for '{prefix}' remaining '{k}' in '{key}'")
                        return default
                    if k not in current:
                        logger.debug(f"Locale: Missing '{k}' in dict at prefix '{prefix}' for key '{key}'")
                        return default
                    current = current[k]
                return current

        # Try direct traversal if no flattened prefix matched (pure nested dict structure)
        current = self._data
        for k in keys:
            if not isinstance(current, dict):
                logger.debug(f"Locale: Traversal stopped at non-dict value for key segment '{k}' in '{key}'")
                return default
            if k not in current:
                logger.debug(f"Locale: Undefined key: '{key}' (missing '{k}')")
                return default
            current = current[k]

        return current if current is not None else default
