"""
SpinRender Logging Utility
Handles log file creation, rotation, and automatic cleanup
"""
import logging
import os
import glob
import time
import subprocess
from datetime import datetime


class SpinLogger:
    """
    Manages date-named logs in the /logs directory
    """
    _LOGGER_NAME = 'SpinRender'
    _CLEANUP_DAYS = 30
    _active_level = None  # Tracks last-initialized level; prevents redundant re-init

    @staticmethod
    def setup(level='info'):
        """
        Configure logging level and file path. No-op if level is unchanged.

        Args:
            level: 'off', 'info', or 'debug'
        """
        # Normalize legacy level names from older saved settings
        _legacy = {'simple': 'info', 'verbose': 'debug'}
        level = _legacy.get(level.lower(), level.lower())

        if SpinLogger._active_level == level:
            return

        # Determine numeric level
        lvl_map = {
            'off': logging.CRITICAL + 1,
            'info': logging.INFO,
            'debug': logging.DEBUG
        }
        numeric_level = lvl_map.get(level, logging.INFO)

        # Get project root and logs directory
        plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logs_dir = os.path.join(plugin_dir, 'logs')
        
        try:
            os.makedirs(logs_dir, exist_ok=True)
        except Exception:
            # Fallback to temp if no write permissions in plugin dir
            import tempfile
            logs_dir = os.path.join(tempfile.gettempdir(), 'SpinRender_Logs')
            os.makedirs(logs_dir, exist_ok=True)

        # Date-based filename: spinrender_2026-03-11.log
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(logs_dir, f'spinrender_{today}.log')

        # Clear existing handlers for our logger
        logger = logging.getLogger(SpinLogger._LOGGER_NAME)
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # If not off, add file handler
        if numeric_level <= logging.CRITICAL:
            try:
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(name)s: %(message)s')
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
                logger.setLevel(numeric_level)
                
                # Also log start of session
                logger.info("--- SpinRender Session Started ---")
            except Exception as e:
                print(f"[SpinRender] Failed to initialize file logger: {e}")

        SpinLogger._active_level = level

        # Always run cleanup
        SpinLogger.cleanup(logs_dir)

    @staticmethod
    def cleanup(logs_dir):
        """Delete log files older than 30 days"""
        if not os.path.exists(logs_dir):
            return

        now = time.time()
        retention_period = SpinLogger._CLEANUP_DAYS * 86400  # 30 days in seconds

        try:
            for log_file in glob.glob(os.path.join(logs_dir, "spinrender_*.log")):
                if os.path.isfile(log_file):
                    file_age = now - os.path.getmtime(log_file)
                    if file_age > retention_period:
                        os.remove(log_file)
        except Exception as e:
            print(f"[SpinRender] Log cleanup error: {e}")

    @staticmethod
    def get_logs_dir():
        """Returns the absolute path to the logs directory"""
        plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logs_dir = os.path.join(plugin_dir, 'logs')
        if not os.path.exists(logs_dir):
            # Fallback path check
            import tempfile
            temp_logs = os.path.join(tempfile.gettempdir(), 'SpinRender_Logs')
            if os.path.exists(temp_logs):
                return temp_logs
        return logs_dir

    @staticmethod
    def open_logs_folder():
        """Opens the logs directory in the system file manager"""
        path = SpinLogger.get_logs_dir()
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

        try:
            if os.name == 'nt': # Windows
                os.startfile(path)
            elif os.uname().sysname == 'Darwin': # macOS
                subprocess.call(['open', path])
            else: # Linux
                subprocess.call(['xdg-open', path])
            return True
        except Exception:
            return False
