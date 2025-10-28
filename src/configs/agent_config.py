import yaml


class AgentConfig:
    def __init__(self, model_config_path: str = "src/configs/model_config.yaml"):
        self.model_config_path = model_config_path
        self.models = self.load_model_configs()

    def load_model_configs(self):
        with open(self.model_config_path, "r") as f:
            models = yaml.safe_load(f)["models"]
        return models

    def format_model_config(self, config: dict):
        return {
            "provider": config.get("provider"),
            "model_name": config.get("model_name"),
            "model_settings": {
                "temperature": config.get("temperature", 0.5),
                "max_tokens": config.get("max_tokens", 8192),
            },
        }

    @property
    def available_models(self):
        return list(self.models.keys())

    @property
    def gpt_mini_config(self):
        config = self.models.get("gpt-5o-mini", {})
        return self.format_model_config(config)

    @property
    def gpt_standard_config(self):
        config = self.models.get("gpt-5o", {})
        return self.format_model_config(config)

    @property
    def gemini_flash_config(self):
        config = self.models.get("gemini-2.5-flash", {})
        return self.format_model_config(config)

    @property
    def gemini_flash_lite_config(self):
        config = self.models.get("gemini-2.5-flash-lite", {})
        return self.format_model_config(config)

    @property
    def gemini_flash_image_config(self):
        config = self.models.get("gemini-2.5-flash-image-preview", {})
        return self.format_model_config(config)
