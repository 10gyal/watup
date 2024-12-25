import os
from openai import OpenAI
from .utils import load_config
from pydantic import BaseModel, Field
from typing import List, Optional


class SystemPrompt(BaseModel):
    system_prompt: str = Field(..., description="The system prompt that corresponds to the user profile.")

class SystemPromptGenerator:
    """
    A class to generate system prompts for various components of the Reddit summarizer.
    """
    def __init__(self, prompt_example: str, save_path: Optional[str] = None):
        config = load_config()
        self.client = OpenAI()
        self.model = config["default_model"]
        self.prompt_example = prompt_example
        self.user_profile = config["user_profile"]
        self.save_path = save_path or config["paths"].get("generated_prompts")
    
    def _save_prompt(self, prompt: str, filename: str) -> None:
        """
        Save a generated prompt to a file.
        
        Args:
            prompt (str): The generated prompt content
            filename (str): Name of the file to save the prompt to
        """
        if not self.save_path:
            return
            
        os.makedirs(self.save_path, exist_ok=True)
        prompt_path = os.path.join(self.save_path, filename)
        
        with open(prompt_path, 'w') as f:
            f.write(prompt)
    
    def generate_prompt(self, save_as: Optional[str] = None) -> str:
        """
        Generate a system prompt for the Reddit summarizer.
        """
        system_message = "You are an expert prompt engineer tasked with creating a system prompt for a Reddit summarizer AI. Your task is to generate a system prompt that guides the AI in summarizing Reddit posts and comments. The system prompt should provide clear instructions on how to summarize posts and comments in a coherent and informative manner. Use the following example as a reference when creating the system prompt:"

        user_message = f"Given the user profile: {self.user_profile}, generate a system prompt similar to the one below: {self.prompt_example}"

        response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                response_format=SystemPrompt,
            )
        
        response = response.choices[0].message.parsed.model_dump()
        response = response["system_prompt"]

        if save_as:
            self._save_prompt(response, save_as)
            print(f"System prompt saved to: {save_as}")

        return response
