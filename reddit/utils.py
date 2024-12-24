"""
Post, Posts, and TopicRecommendations classes for handling Reddit data
"""
from typing import Dict, Any, List
import json
import os

def load_config() -> Dict[str, Any]:
    """Load configuration from config.json"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

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

class TopicRecommendations:
    def __init__(self, path: str):
        self.path = path
        self.themes: List[Dict[str, Any]] = []
        self._load_themes()
    
    def _load_themes(self):
        """Load themes from the JSON file"""
        with open(self.path, "r") as file:
            data = json.load(file)
            self.themes = data["themes"]
    
    def get_themes(self) -> List[Dict[str, Any]]:
        """Get list of theme dictionaries"""
        return self.themes
    
    def get_post_ids_for_theme(self, theme: str) -> List[str]:
        """Get post IDs for a specific theme"""
        for theme_data in self.themes:
            if theme_data["theme"] == theme:
                return theme_data["post_ids"]
        return []
