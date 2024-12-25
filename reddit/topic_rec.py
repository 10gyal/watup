"""
Recommend topics based on top posts + comments across subreddits
"""
from pydantic import BaseModel, Field
from typing import List
from openai import OpenAI
from .utils import Post, Posts, DailyPosts
from .prompts.topic_recommender_prompt import SYSTEM_MESSAGE

class Theme(BaseModel):
    theme: str = Field(..., description="Recommended theme for the day")
    post_id: str = Field(..., description="Post ID of the post related to the theme")

class Topics(BaseModel):
    themes: List[Theme] = Field(..., description="4-5 top recommended themes for the day")

class TopicRecommender:
    def __init__(self, path: str = "/Users/tashi/Desktop/projects/whatsup/reddit_data.json"):
        self.client = OpenAI()
        self.path = path
    
    def recommend_topics(self):
        """
        Analyze posts and recommend trending topics
        """
        posts_text = DailyPosts(self.path).gather_posts()
        
        response = self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": posts_text},
            ],
            response_format=Topics,
        )

        response = response.choices[0].message.parsed
        response = response.model_dump()
        return response
