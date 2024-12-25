"""
Module for summarizing comments from Reddit posts grouped by themes
"""
from typing import Dict, List, Optional
import praw
import json
from pydantic import BaseModel, Field
from openai import OpenAI
from .auth import get_reddit_instance
from .utils import load_config
from .prompts.comment_summarizer_prompt import SYSTEM_MESSAGE


class CommentSummary(BaseModel):
    comment_summary: str = Field(..., description="Summary of the comment discussion")

class CommentSummarizer:
    """
    A class to summarize Reddit comments grouped by themes.
    
    This class processes comments from posts within themes and generates concise summaries
    focusing on technical details and key points for an engineer audience.
    """
    def __init__(self, 
                 summaries_path: str = None,
                 output_path: str = None):
        config = load_config()
        self.client = OpenAI()
        self.summaries_path = summaries_path or config["paths"]["theme_summaries"]
        self.output_path = output_path or config["paths"]["comment_summaries"]
        self.model = config["summarizer"]["comment"]["model"]
        self.max_comments = config["summarizer"]["comment"]["max_comments_per_post"]
        self.max_replies = config["summarizer"]["comment"]["max_replies_per_comment"]
        self.system_message = SYSTEM_MESSAGE

    def get_comments_for_post(self, reddit: praw.Reddit, post_id: str, max_comments: int = None) -> List[str]:
        """
        Get comments and their replies for a specific post.
        
        Args:
            reddit: Authenticated Reddit instance
            post_id: ID of the Reddit post
            max_comments: Maximum number of top-level comments to fetch (defaults to config value)
            
        Returns:
            List of formatted comment strings including replies
        """
        try:
            submission = reddit.submission(id=post_id)
            submission.comments.replace_more(limit=0)  # Remove MoreComments objects
            
            comments = []
            for comment in submission.comments[:max_comments or self.max_comments]:
                # Format the top-level comment
                comment_text = f"[Score: {comment.score}] {comment.body}"
                comments.append(comment_text)
                
                # Get replies
                if comment.replies:
                    for reply in comment.replies[:self.max_replies]:
                        if isinstance(reply, praw.models.Comment):
                            reply_text = f"  ↳ [Score: {reply.score}] {reply.body}"
                            comments.append(reply_text)
            
            return comments
        except Exception as e:
            print(f"Error fetching comments for post {post_id}: {str(e)}")
            return []

    def get_theme_comments(self, reddit: praw.Reddit, theme: Dict[str, any]) -> Dict[str, List[str]]:
        """
        Get comments for all posts in a theme.
        
        Args:
            reddit: Authenticated Reddit instance
            theme: Theme dictionary containing theme name and post IDs
            
        Returns:
            Dictionary mapping post IDs to their comments
        """
        theme_comments = {}
        for post_id in theme["post_ids"]:
            comments = self.get_comments_for_post(reddit, post_id)
            if comments:
                theme_comments[post_id] = comments
        return theme_comments

    def summarize_comments(self) -> Optional[Dict[str, Dict]]:
        """
        Main function to summarize comments for all themes and their posts.
        
        Returns:
            Dictionary mapping themes to their posts' comments and summaries, or None if authentication fails
        """
        # Get authenticated Reddit instance
        reddit = get_reddit_instance()
        if not reddit:
            print("Failed to authenticate with Reddit")
            return None
            
        # Load themes from theme summaries
        try:
            with open(self.summaries_path, "r") as f:
                themes = json.load(f)
        except Exception as e:
            print(f"Error loading {self.summaries_path}: {str(e)}")
            return None
        
        # Get comments for each theme
        theme_summaries = {}
        for theme in themes:
            theme_name = theme["theme"]
            print(f"Processing theme: {theme_name}")
            
            theme_comments = self.get_theme_comments(reddit, theme)
            if theme_comments:
                theme_summaries[theme_name] = {
                    "post_summary": theme["post_summary"],
                    "comments": theme_comments
                }
        
        # Generate summaries for each theme
        final_summaries = []
        for theme_name, data in theme_summaries.items():
            concat_comments = data["post_summary"] + "\n\nComments:\n"
            for post_id, comments in data["comments"].items():
                for comment in comments:
                    concat_comments += comment + "\n"            
            
            try:
                response = self.client.beta.chat.completions.parse(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.system_message},
                        {"role": "user", "content": concat_comments},
                    ],
                    response_format=CommentSummary,
                )
                response = response.choices[0].message.parsed.model_dump()
                
                final_summary = {
                    "theme": theme_name,
                    "post_summary": data["post_summary"],
                    "comment_summary": response["comment_summary"]
                }
                final_summaries.append(final_summary)
            except Exception as e:
                print(f"Error generating summary for theme {theme_name}: {str(e)}")
                continue
        
        # Save summaries
        try:
            with open(self.output_path, "w") as f:
                json.dump(final_summaries, indent=2, ensure_ascii=False, fp=f)
        except Exception as e:
            print(f"Error saving summaries to {self.output_path}: {str(e)}")
        
        return final_summaries

if __name__ == "__main__":
    summarizer = CommentSummarizer()
    summaries = summarizer.summarize_comments()
