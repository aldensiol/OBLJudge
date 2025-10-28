from src.agents.base import BaseAgent
from src.configs import agent_config
from src.outputs import JudgeOutput
from src.prompts import JUDGE_SYSTEM_PROMPT, JUDGE_INSTRUCTIONS


class JudgeAgent(BaseAgent):
    def __init__(self):
        config = agent_config.gemini_flash_lite_config
        super().__init__(
            provider=config["provider"],
            model_name=config["model_name"],
            system_prompt=JUDGE_SYSTEM_PROMPT,
            instructions=JUDGE_INSTRUCTIONS,
            output_type=JudgeOutput,
            model_settings=config["model_settings"],
        )
