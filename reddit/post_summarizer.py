from pydantic import BaseModel, Field
from typing import List, Dict, Any
from openai import OpenAI

"""
summarize the post body + top 5 comments (not replies to the comments)
"""

class PostSummary(BaseModel):
    




class PostSummarizer:
    def __init__(self, post):
        self.post = post
        self.comments = post.comments[:5]
        self.client = OpenAI()

    def create_post_content(self):
        # post body + top 5 comments
        post_body = self.post.body
        comments = [comment.body for comment in self.comments]
        post_content = post_body + ' '.join(comments)
        return post_content
    
    def summarize(self):
        client = self.client
        post_content = self.create_post_content()
        response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": ""},
                {"role": "user", "content": post_content},
            ],
            response_format=,
        )
        
        response = response.choices[0].message.parsed
        response = response.model_dump()
        is_informative = response.get("is_informative", False)
        print(f"Post content analyzed. is_informative: {is_informative}")
        return is_informative