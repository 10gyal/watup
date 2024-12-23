"""
Post and Posts classes for handling Reddit post data
"""
from typing import Dict, Any, List
import json

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

class Posts:
    def __init__(self, path: str):
        self.path = path
        self.posts: List[Post] = []
        self._load_posts()
    
    def _load_posts(self):
        """Load posts from the JSON file"""
        with open(self.path, "r") as file:
            posts_data = json.load(file)
        self.posts = [Post(post) for post in posts_data]
    
    def get_posts(self) -> List[Post]:
        """Get list of Post objects"""
        return self.posts
    
    def __repr__(self):
        return "\n---\n".join(post.stringify() for post in self.posts)

class DailyPosts(Posts):
    def gather_posts(self) -> str:
        """Get posts as a formatted string with separators"""
        return "\n---\n".join(post.stringify() for post in self.posts)
