import json
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List
from .utils import load_config
from dotenv import load_dotenv
import os

load_dotenv()


class UserProfileResponse(BaseModel):
    user_profile: str = Field(..., description="User profile based on the user's interests and intent.")
    expertise_level: str = Field(..., description="Expertise level of the user profile")
    reason: str = Field(..., description="Reasoning behind expertise level")

class UserProfile:
    def __init__(self, who, interest, intent):
        self.client = OpenAI()
        self.who = who
        self.interest = interest
        self.intent = intent
    
    def generate_profile(self):
        """
        Generate a user profile based on the user's interests and intent.
        """
        system_message = """You are a professional consultant that helps users articulate their learning goals for career growth. First, understand the level of expertise the user might have. Choose one level from the following and then provide a concise reason for your choice:
        {
            "beginner": "You are new to the field or subject and have limited knowledge or experience. You might have taken an introductory course, read some materials, or started exploring the basics.",
            "intermediate": "You have a foundational understanding and some practical experience in the field. You are confident in basic tasks and concepts but seek to deepen your knowledge and handle more complex challenges.",
            "proficient": "You are skilled and experienced in the field, capable of working independently on a wide range of tasks. You’re looking to refine your expertise and take on leadership or specialized roles.",
            "expert": "You are a highly experienced professional with deep expertise in your field. You are a thought leader or specialist, frequently driving innovation, mentoring others, or leading high-impact initiatives."
        }
        Your task is to generate a user profile that reflects the user's interests and intent. The user profile should provide clear and concise information on who the user is, what they are interested in, and what their intentions are."""
        
        user_message = f"Given the user profile: {self.who}, {self.interest}, {self.intent}, generate a user profile similar to the one below:"
        
        response = self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            response_format=UserProfileResponse,
        )
        
        response = response.choices[0].message.parsed.model_dump()
        return response
    
    def save_to_json(self, profile: str) -> None:
        """
        Save the generated profile to a JSON file.
        """
        output = {
            "profile": profile["user_profile"],
            "metadata": {
                "expertise_level": profile["expertise_level"],
                "reason": profile["reason"]
            }
        }
        
        with open('user_profile.json', 'w') as f:
            json.dump(output, f, indent=4)

if __name__ == "__main__":
    user_profile = load_config()["user_profile"]
    user_profile = UserProfile(**user_profile)
    profile = user_profile.generate_profile()
    user_profile.save_to_json(profile)
    print(f"Profile generated and saved to user_profile.json")
