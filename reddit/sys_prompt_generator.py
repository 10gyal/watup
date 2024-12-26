import os
import json
from openai import OpenAI
from .utils import load_config
from pydantic import BaseModel, Field
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

class SystemPrompt(BaseModel):
    response: str = Field(..., description="System prompt containing user profile, task description, example, and remarks")

class SystemPromptGenerator:
    """
    A class to generate system prompts for various components of the Reddit summarizer.
    """
    def __init__(self, prompt_example: str, save_path: Optional[str] = None):
        config = load_config()
        self.client = OpenAI()
        self.model = config["default_model"]
        self.prompt_example = prompt_example
        self.save_path = save_path or config["paths"].get("generated_prompts")
        
        # Load user profile from JSON
        try:
            with open('user_profile.json', 'r') as f:
                self.user_profile_data = json.load(f)

        except FileNotFoundError:
            raise FileNotFoundError("user_profile.json not found. Please run create_user_profile.py first.")
    
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
        system_message = "You are an expert prompt engineer tasked with creating a system prompt from the given example. Your task is to generate a system prompt that aligns well with the user profile or target audience and therefore the user profile must be clearly mentioned in the system prompt. The system prompt should provide clear descriptions on who the target audience is, what the task is, what are some examples and additional remarks if given in the example. Use the following example as a reference when creating the system prompt for the given user:"

        user_message = f"Given the user profile: {self.user_profile_data}, generate a system prompt that follows the template below: {self.prompt_example}"

        response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                response_format=SystemPrompt,
            )
        
        response = response.choices[0].message.parsed.model_dump()
        response = response["response"]

        if save_as:
            self._save_prompt(response, save_as)
            print(f"System prompt saved to: {save_as}")

        return response
