"""
SpinRender Preset Management System
Handles saving, loading, and managing render presets
"""
import json
import os
import logging
from pathlib import Path

logger = logging.getLogger("SpinRender")

try:
    from SpinRender.core.settings import RenderSettings
except ImportError:
    RenderSettings = None  # For backward compatibility if used standalone


class PresetManager:
    """
    Manages render presets for SpinRender
    """

    def __init__(self, board_path=None):
        """
        Initialize preset manager

        Args:
            board_path: Optional path to board file for project-specific presets
        """
        self.board_path = board_path

        # Global presets directory (in user home)
        self.global_presets_dir = os.path.join(
            Path.home(),
            '.spinrender',
            'presets'
        )
        os.makedirs(self.global_presets_dir, exist_ok=True)

        # Project presets directory (next to board file)
        if board_path:
            board_dir = os.path.dirname(board_path)
            self.project_presets_dir = os.path.join(board_dir, '.spinrender')
            os.makedirs(self.project_presets_dir, exist_ok=True)
        else:
            self.project_presets_dir = None

    def save_preset(self, name, settings, is_global=False):
        """
        Save a preset

        Args:
            name: Preset name
            settings: RenderSettings object or dict of render settings
            is_global: If True, save to global presets; otherwise project presets

        Returns:
            bool: True if successful
        """
        # Sanitize preset name
        safe_name = "".join(c for c in name if c.isalnum() or c in ('-', '_')).lower()
        if not safe_name:
            raise ValueError("Invalid preset name")

        # Determine save location
        if is_global or not self.project_presets_dir:
            preset_dir = self.global_presets_dir
        else:
            preset_dir = self.project_presets_dir

        # Save preset
        preset_path = os.path.join(preset_dir, f"{safe_name}.json")

        # Convert RenderSettings to dict, or use dict directly
        if RenderSettings is not None and isinstance(settings, RenderSettings):
            settings_dict = settings.to_dict()
        elif isinstance(settings, dict):
            settings_dict = settings
        else:
            raise TypeError(f"settings must be RenderSettings or dict, got {type(settings)}")

        preset_data = {
            'name': name,
            'settings': settings_dict
        }

        try:
            with open(preset_path, 'w') as f:
                json.dump(preset_data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save preset: {e}", exc_info=True)
            return False

    def load_preset(self, name, is_global=False):
        """
        Load a preset

        Args:
            name: Preset name (or filename without extension)
            is_global: If True, load from global presets

        Returns:
            RenderSettings: Preset settings, or None if not found
        """
        # Sanitize name
        safe_name = "".join(c for c in name if c.isalnum() or c in ('-', '_')).lower()

        # Determine load location
        if is_global or not self.project_presets_dir:
            preset_dir = self.global_presets_dir
        else:
            preset_dir = self.project_presets_dir

        preset_path = os.path.join(preset_dir, f"{safe_name}.json")

        if not os.path.exists(preset_path):
            return None

        try:
            with open(preset_path, 'r') as f:
                preset_data = json.load(f)
            settings_dict = preset_data.get('settings', {})

            # Convert to RenderSettings if available
            if RenderSettings is not None:
                return RenderSettings.from_dict(settings_dict)
            return settings_dict
        except Exception as e:
            logger.error(f"Failed to load preset: {e}", exc_info=True)
            return None

    def list_presets(self, include_global=True):
        """
        List available presets

        Args:
            include_global: If True, include global presets

        Returns:
            list: List of preset names
        """
        presets = []

        # Project presets
        if self.project_presets_dir and os.path.exists(self.project_presets_dir):
            for filename in os.listdir(self.project_presets_dir):
                if filename.endswith('.json'):
                    preset_name = filename[:-5]  # Remove .json
                    if preset_name.lower() != "last_used":
                        presets.append(('project', preset_name))

        # Global presets
        if include_global and os.path.exists(self.global_presets_dir):
            for filename in os.listdir(self.global_presets_dir):
                if filename.endswith('.json'):
                    preset_name = filename[:-5]
                    if preset_name.lower() != "last_used":
                        presets.append(('global', preset_name))

        return presets

    def delete_preset(self, name, is_global=False):
        """
        Delete a preset

        Args:
            name: Preset name
            is_global: If True, delete from global presets

        Returns:
            bool: True if successful
        """
        safe_name = "".join(c for c in name if c.isalnum() or c in ('-', '_')).lower()

        if is_global or not self.project_presets_dir:
            preset_dir = self.global_presets_dir
        else:
            preset_dir = self.project_presets_dir

        preset_path = os.path.join(preset_dir, f"{safe_name}.json")

        if os.path.exists(preset_path):
            try:
                os.remove(preset_path)
                return True
            except Exception as e:
                logger.error(f"Failed to delete preset: {e}", exc_info=True)
                return False

        return False

    def get_last_used_settings(self):
        """
        Get the last used render settings.
        Tries project-specific first, then falls back to global.

        Returns:
            RenderSettings: Last used settings, or None
        """
        # 1. Try project-specific settings first
        if self.project_presets_dir:
            project_path = os.path.join(self.project_presets_dir, 'last_used.json')
            if os.path.exists(project_path):
                try:
                    with open(project_path, 'r') as f:
                        data = json.load(f)
                    if RenderSettings is not None:
                        return RenderSettings.from_dict(data)
                    return data
                except Exception as e:
                    logger.error(f"Failed to load project last used settings: {e}", exc_info=True)

        # 2. Fallback to global last used settings
        global_path = os.path.join(self.global_presets_dir, 'last_used.json')
        if os.path.exists(global_path):
            try:
                with open(global_path, 'r') as f:
                    data = json.load(f)
                if RenderSettings is not None:
                    return RenderSettings.from_dict(data)
                return data
            except Exception as e:
                logger.error(f"Failed to load global last used settings: {e}", exc_info=True)

        return None

    def save_last_used_settings(self, settings):
        """
        Save the last used render settings.
        Saves to both project-specific (if available) and global locations.

        Args:
            settings: RenderSettings object or dict of render settings

        Returns:
            bool: True if global save was successful
        """
        # Convert RenderSettings to dict if needed
        if RenderSettings is not None and isinstance(settings, RenderSettings):
            settings_dict = settings.to_dict()
        elif isinstance(settings, dict):
            settings_dict = settings
        else:
            raise TypeError(f"settings must be RenderSettings or dict, got {type(settings)}")

        success = True

        # 1. Save to project-specific directory if it exists
        if self.project_presets_dir:
            project_path = os.path.join(self.project_presets_dir, 'last_used.json')
            try:
                with open(project_path, 'w') as f:
                    json.dump(settings_dict, f, indent=2)
            except Exception as e:
                logger.error(f"Failed to save project last used settings: {e}", exc_info=True)
                success = False

        # 2. Always save to global directory for cross-project persistence
        global_path = os.path.join(self.global_presets_dir, 'last_used.json')
        try:
            with open(global_path, 'w') as f:
                json.dump(settings_dict, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save global last used settings: {e}", exc_info=True)
            success = False

        return success
