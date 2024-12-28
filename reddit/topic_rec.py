"""
Recommend topics based on top posts + comments across subreddits
"""
import os
from pydantic import BaseModel, Field
from typing import List
from openai import OpenAI
from .utils import Post, Posts, DailyPosts, load_config

class Theme(BaseModel):
    theme: str = Field(..., description="Recommended theme for the day")
    post_id: str = Field(..., description="The post_id of the single most relevant post for the theme")
    url: str = Field(..., description="The URL of the most relevant post for the theme")

class Topics(BaseModel):
    themes: List[Theme] = Field(..., description="4-5 top recommended themes for the day")

class TopicRecommender:
    def __init__(self, path: str = "/Users/tashi/Desktop/projects/whatsup/reddit_data.json"):
        self.client = OpenAI()
        self.path = path
        config = load_config()
        prompt_path = os.path.join(config["paths"]["generated_prompts"], "topic_recommender_prompt.txt")
        with open(prompt_path, 'r') as f:
            self.system_prompt = f.read()
    
    def recommend_topics(self):
        """
        Analyze posts and recommend trending topics
        """
        posts_text = DailyPosts(self.path).gather_posts()
        
        response = self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": posts_text},
            ],
            response_format=Topics,
        )

        response = response.choices[0].message.parsed
        response = response.model_dump()
        
        # Load posts to get URLs
        posts = DailyPosts(self.path).get_posts()
        post_urls = {post.post_id: post.url for post in posts}
        
        for theme in response["themes"]:
            post_id = theme["post_id"]
            theme["post_id"] = [post_id]  # Convert to list format
            theme["url"] = post_urls[post_id]  # Add URL for the post

        return response
