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

    # ------------------------------
    # Centralized template management
    # ------------------------------
    def ensure_default_template(self):
        """Ensure the default template and structure exist in the config."""
        cfg = self.config
        templates = cfg.setdefault('templates', {})
        if 'Default' not in templates:
            templates['Default'] = {
                'text': 'Your Watermark',
                'font_size': 40,           # fallback value when no image is selected
                'font_size_auto': True,    # default template uses auto font sizing
                'opacity': 50,             # 0-100 percent
                'color': [255, 255, 255],  # RGB list for JSON compatibility
                'position_mode': 'bottom-right',
                'offset_x': 0,
                'offset_y': 0
            }
        cfg.setdefault('selected_template', 'Default')
        self.save_config()

    def list_templates(self):
        """Return a list of template names, with 'Default' first."""
        names = list(self.config.get('templates', {}).keys())
        if 'Default' in names:
            names.remove('Default')
            return ['Default'] + sorted(names)
        return sorted(names)

    def get_template(self, name):
        """Get a template by name, or None if missing."""
        return self.config.get('templates', {}).get(name)

    def add_template(self, name, settings):
        """Add a new template. 'Default' cannot be added or modified here."""
        if not name:
            raise ValueError("Template name cannot be empty")
        if name == 'Default':
            raise ValueError("Default template cannot be modified")
        templates = self.config.setdefault('templates', {})
        if name in templates:
            raise ValueError("A template with this name already exists")
        templates[name] = settings
        self.save_config()

    def update_template(self, name, settings):
        """Update an existing template. 'Default' cannot be modified."""
        if name == 'Default':
            raise ValueError("Default template cannot be modified")
        templates = self.config.setdefault('templates', {})
        if name not in templates:
            raise ValueError("Template does not exist")
        templates[name] = settings
        self.save_config()

    def delete_template(self, name):
        """Delete a template by name. 'Default' cannot be deleted."""
        if name == 'Default':
            raise ValueError("Default template cannot be deleted")
        templates = self.config.setdefault('templates', {})
        if name in templates:
            del templates[name]
            # If the deleted template was selected, fall back to Default
            if self.config.get('selected_template') == name:
                self.config['selected_template'] = 'Default'
            self.save_config()
        else:
            raise ValueError("Template does not exist")

    def set_selected_template(self, name):
        """Set the currently selected template if it exists, otherwise default."""
        if name in self.config.get('templates', {}):
            self.config['selected_template'] = name
        else:
            self.config['selected_template'] = 'Default'
        self.save_config()

    def get_selected_template_name(self):
        """Get the name of the selected template (default if not set)."""
        return self.config.get('selected_template', 'Default')