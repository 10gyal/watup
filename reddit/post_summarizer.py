"""
Summarize Reddit posts based on themes
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from openai import OpenAI
from .utils import DailyPosts, Posts, Post, TopicRecommendations, load_config
from dotenv import load_dotenv
from .prompts.post_summarizer_prompt import SYSTEM_MESSAGE

load_dotenv()

class PostSummary(BaseModel):
    post_summary: str = Field(
        ..., 
        description="Summary of the post content including key points, technical details, and relevant links"
    )

class PostSummarizer:
    """
    A class to summarize Reddit posts grouped by themes.
    
    This class processes posts from specified themes and generates concise summaries
    focusing on technical details and key points for an engineer audience.
    """
    def __init__(self, 
                 content_path: str = None,
                 theme_path: str = None):
        config = load_config()
        self.client = OpenAI()
        self.content_path = content_path or config["paths"]["reddit_data_json"]
        self.theme_path = theme_path or config["paths"]["topic_recommendations"]
        self.model = config["summarizer"]["post"]["model"]
        self.system_message = SYSTEM_MESSAGE
    
    def summarize_theme_posts(self, theme_index: int = 0) -> Dict[str, Any]:
        """
        Summarize posts for a specific theme.
        
        Args:
            theme_index: Index of the theme to summarize (default: 0)
            
        Returns:
            Dictionary containing the theme, post IDs, and summary with format:
            {
                'theme': str,  # The theme name
                'post_ids': List[str],  # List of post IDs in this theme
                'summary': str  # The generated summary text
            }
            
        Raises:
            ValueError: If theme_index is out of range or no posts found for theme
        """
        try:
            # Load posts and themes
            posts = Posts(self.content_path)
            all_posts = {post.post_id: post for post in posts.get_posts()}
            
            themes = TopicRecommendations(self.theme_path).get_themes()
            if not themes:
                raise ValueError("No themes found in the recommendations file")
            if theme_index >= len(themes):
                raise ValueError(f"Theme index {theme_index} is out of range (max: {len(themes)-1})")
                
            # Gather post contents for the theme
            theme = themes[theme_index]
            post_contents = ""
            for post_id in theme["post_ids"]:
                if post_id in all_posts:
                    post = all_posts[post_id]
                    post_contents += f"[Post ID: {post.post_id}]\n{post.content}\n\n"
                    
            if not post_contents:
                raise ValueError(f"No posts found for theme '{theme['theme']}'")
            
            # Generate summary
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_message},
                    {"role": "user", "content": post_contents},
                ],
                response_format=PostSummary,
            )
            
            response = response.choices[0].message.parsed.model_dump()
            response = response["post_summary"]

            result = {
                'theme': theme['theme'],
                'post_ids': theme['post_ids'],
                'post_summary': response
            }
            
            self.save_summary_to_json(result)
            return result
            
        except Exception as e:
            print(f"Error summarizing posts: {str(e)}")
            raise
            
    def save_summary_to_json(self, summary_data: Dict[str, Any], output_path: str = None) -> None:
        """
        Save the theme summary data to a JSON file.
        
        Args:
            summary_data: Dictionary containing theme, post IDs, and summary
            output_path: Path to save the JSON file (default: theme_summaries.json)
        """
        import json
        import os
        
        try:
            config = load_config()
            final_path = output_path or config["paths"]["theme_summaries"]
            
            # Load existing summaries if file exists
            existing_summaries = []
            if os.path.exists(final_path):
                with open(final_path, 'r') as f:
                    existing_summaries = json.load(f)
            
            # Update or add new summary
            theme_exists = False
            for i, summary in enumerate(existing_summaries):
                if summary['theme'] == summary_data['theme']:
                    existing_summaries[i] = summary_data
                    theme_exists = True
                    break
            
            if not theme_exists:
                existing_summaries.append(summary_data)
            
            # Save updated summaries
            with open(final_path, 'w') as f:
                json.dump(existing_summaries, indent=2, ensure_ascii=False, fp=f)
                
        except Exception as e:
            print(f"Error saving summary to JSON: {str(e)}")
            raise
