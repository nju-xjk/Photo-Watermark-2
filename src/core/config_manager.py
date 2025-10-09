import json

class ConfigManager:
    """Manages loading and saving of watermark templates."""

    def __init__(self, config_file='config.json'):
        self.config_file = config_file

    def save_template(self, template_name, watermark):
        """Saves a watermark template."""
        # Placeholder for saving template
        print(f"Saving template '{template_name}'")

    def load_template(self, template_name):
        """Loads a watermark template."""
        # Placeholder for loading template
        print(f"Loading template '{template_name}'")
        return None

    def load_last_settings(self):
        """Loads the last used settings."""
        # Placeholder for loading last settings
        print("Loading last settings")
        return None