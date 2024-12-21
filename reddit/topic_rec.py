"""
Recommend topics based on top posts + comments across subreddits
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from openai import OpenAI
import json

class Topics(BaseModel):
    theme: str = Field(..., title="Theme of the day")
    post_id: List[str] = Field(..., title="list of related post_ids")
    post_topics: List[str] = Field(..., title="Topics covered in the post")

class Post:
    def __init__(self, post: Dict[str, Any]):
        self.post_id = post["post_id"]
        self.content = post["post_content"]
        self.comments = post["comments"]
        self.subreddit = post["subreddit"]
        self.score = post["score"]
    
    def stringify(self) -> str:
        return f"Post: {self.post_id}\nContent: {self.content}\nComments: {self.comments}\nSubreddit: {self.subreddit}\nScore: {self.score}"
    
    def __repr__(self):
        return self.stringify()

class TopicRecommender:
    def __init__(self, path):
        self.path = path
        self.client = OpenAI()

    def gather_posts(self) -> str:
        with open(self.path, "r") as file:
            posts_data = json.load(file)
        
        posts = [Post(post) for post in posts_data]
        print("*"*50)
        print("Posts gathered: ", posts)
        print("*"*50)
        return "\n---\n".join(post.stringify() for post in posts)
    
    def recommend_topics(self, num_topics: int = 5) -> List[str]:
        """
        Analyze posts and recommend trending topics
        """
        posts_text = self.gather_posts()
        
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