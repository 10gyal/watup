"""
Recommend topics based on top posts + comments across subreddits
"""
from pydantic import BaseModel, Field
from typing import List
from openai import OpenAI
from .posts import Post, Posts, DailyPosts

class Theme(BaseModel):
    theme: str = Field(..., description="Recommended theme for the day")
    post_ids: List[str] = Field(..., description="Post IDs of the posts related to the theme")

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
        
        system_message = f"""
        You are a summarizer AI designed to integrate important discussion topics (and only important) across a Reddit subreddit about AI for **a technical, detail oriented engineer audience**.
        Your task is to create a unified summary that captures key points, conversations, and references without being channel-specific. Focus on thematic coherence and group similar discussion points, even if they are from different posts.
        <IMPORTANT>
        Your task is to identify 4-5 top themes, filtered for interestingness, technical depth, and detailed, excited discussion, special attention to the posts scoring over 500 points, new fundraising, new models, and new tooling. Ignore mundane troubleshooting, bug reports, discussions about politics, alignment, AI Safety, AGI discussions about the distant future. For each Theme, you are then to identify the most relevant posts for that theme, taking EXTRA CARE to provide the exact post_id.
        Your themes should be very specific, naming specific models and developments and trends, condensing the insight in a single short headline, for example in the form of:
        - California's SB 1047: Implications for AI Development
        - InternLM2.5-1M gets 100% recall at 1M Context
        - Criticsm of "Gotcha" tests to determine LLM intelligence
        - Open-Source Text-to-Video AI: CogVideoX 5B Breakthrough
        - Gemini 1.5 Flash 8B released, outperforming Llama 2 70B
        - Tinybox now on sale: 8x A100 80GB GPUs with NVLink and 400Gbps networking
        You want to have themes that actually name the models and developments and trends rather than just the broad category.
        </IMPORTANT>
        You are going to first be given a full data dump of all reddit posts today, and second given your previous selection of 4-5 focus themes of the day.
        Your task is to then provide the exact post_id and proposed postTopics of 2-4 posts corresponding to the selected theme, for each theme.
        """
        
        response = self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": posts_text},
            ],
            response_format=Topics,
        )

        response = response.choices[0].message.parsed
        response = response.model_dump()
        return response
