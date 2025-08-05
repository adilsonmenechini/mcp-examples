import yaml
from typing import Dict, Any
import os


class ConfigHandler:
    def __init__(self, server_name: str, config_path: str = None):
        self.server_name = server_name
        self.config_path = config_path or "config.yaml"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)

            # Ensure basic structure exists
            if not config:
                config = {}

            # Add default logging configuration if not present
            if "logging" not in config:
                config["logging"] = self._default_logging_config()

            # Add default retry configuration if not present
            if "retry" not in config:
                config["retry"] = self._default_retry_config()

            # Add default cache configuration if not present
            if "cache" not in config:
                config["cache"] = self._default_cache_config()

            return config

        except FileNotFoundError:
            # Create default config if file doesn't exist
            config = {
                "logging": self._default_logging_config(),
                "retry": self._default_retry_config(),
                "cache": self._default_cache_config(),
            }
            self._save_config(config)
            return config
        except Exception as e:
            raise Exception(f"Failed to load config: {str(e)}")

    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to YAML file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

            with open(self.config_path, "w") as f:
                yaml.dump(config, f, default_flow_style=False)
        except Exception as e:
            raise Exception(f"Failed to save config: {str(e)}")

    def _default_logging_config(self) -> Dict[str, Any]:
        """Get default logging configuration"""
        return {
            "level": "INFO",
            "format": "json",
            "file": f"{self.server_name.lower()}.log",
            "max_size": 10485760,  # 10MB
            "backup_count": 5,
        }

    def _default_retry_config(self) -> Dict[str, Any]:
        """Get default retry configuration"""
        return {
            "max_attempts": 3,
            "delay": 1,  # seconds
            "backoff_factor": 2,
        }

    def _default_cache_config(self) -> Dict[str, Any]:
        """Get default cache configuration"""
        return {
            "enabled": True,
            "ttl": 300,  # seconds
            "max_size": 1000,  # entries
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        try:
            keys = key.split(".")
            value = self.config
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """Set configuration value by key"""
        try:
            keys = key.split(".")
            config = self.config
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            config[keys[-1]] = value
            self._save_config(self.config)
        except Exception as e:
            raise Exception(f"Failed to set config value: {str(e)}")

    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple configuration values"""
        try:

            def deep_update(d: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
                for k, v in u.items():
                    if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                        d[k] = deep_update(d[k], v)
                    else:
                        d[k] = v
                return d

            self.config = deep_update(self.config, updates)
            self._save_config(self.config)
        except Exception as e:
            raise Exception(f"Failed to update config: {str(e)}")

    def validate_required(self, required_keys: list) -> None:
        """Validate that required configuration keys exist"""
        missing = []
        for key in required_keys:
            if self.get(key) is None:
                missing.append(key)
        if missing:
            raise Exception(
                f"Missing required configuration keys: {', '.join(missing)}"
            )

    def ensure_paths(self, paths: list) -> None:
        """Ensure required paths exist"""
        for path in paths:
            path_value = self.get(path)
            if path_value:
                os.makedirs(os.path.dirname(path_value), exist_ok=True)
