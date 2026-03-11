"""
SpinRender Preset Management System
Handles saving, loading, and managing render presets
"""
import json
import os
from pathlib import Path


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
            settings: Dict of render settings
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

        preset_data = {
            'name': name,
            'settings': {
                'tilt': settings.get('tilt', 45.0),
                'period': settings.get('period', 10.0),
                'easing': settings.get('easing', 'linear'),
                'direction': settings.get('direction', 'ccw'),
                'lighting': settings.get('lighting', 'studio'),
                'rotate_z': settings.get('rotate_z', -45.0)
            }
        }

        try:
            with open(preset_path, 'w') as f:
                json.dump(preset_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save preset: {e}")
            return False

    def load_preset(self, name, is_global=False):
        """
        Load a preset

        Args:
            name: Preset name (or filename without extension)
            is_global: If True, load from global presets

        Returns:
            dict: Preset settings, or None if not found
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
            return preset_data.get('settings', {})
        except Exception as e:
            print(f"Failed to load preset: {e}")
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
                    presets.append(('project', preset_name))

        # Global presets
        if include_global and os.path.exists(self.global_presets_dir):
            for filename in os.listdir(self.global_presets_dir):
                if filename.endswith('.json'):
                    preset_name = filename[:-5]
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
                print(f"Failed to delete preset: {e}")
                return False

        return False

    def get_last_used_settings(self):
        """
        Get the last used render settings for this project

        Returns:
            dict: Last used settings, or None
        """
        if not self.project_presets_dir:
            return None

        settings_path = os.path.join(self.project_presets_dir, 'last_used.json')

        if not os.path.exists(settings_path):
            return None

        try:
            with open(settings_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load last used settings: {e}")
            return None

    def save_last_used_settings(self, settings):
        """
        Save the last used render settings for this project

        Args:
            settings: Dict of render settings

        Returns:
            bool: True if successful
        """
        if not self.project_presets_dir:
            return False

        settings_path = os.path.join(self.project_presets_dir, 'last_used.json')

        try:
            with open(settings_path, 'w') as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save last used settings: {e}")
            return False
