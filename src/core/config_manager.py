import json

class ConfigManager:
    """Manages application configuration and watermark templates."""

    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        """Loads the application configuration."""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}

    def save_config(self):
        """Saves the application configuration."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get_setting(self, key, default=None):
        """Gets a setting from the configuration."""
        return self.config.get(key, default)

    def set_setting(self, key, value):
        """Sets a setting in the configuration."""
        self.config[key] = value
        self.save_config()

    def save_watermark_template(self, settings, filepath):
        """Saves watermark settings to a JSON file."""
        try:
            with open(filepath, 'w') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Error saving template {filepath}: {e}")

    def load_watermark_template(self, filepath):
        """Loads watermark settings from a JSON file."""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Template file not found: {filepath}")
            return None
        except Exception as e:
            print(f"Error loading template {filepath}: {e}")
            return None