"""
Summarize Reddit posts based on themes
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from openai import OpenAI
from .utils import DailyPosts, Posts, Post, TopicRecommendations
from dotenv import load_dotenv

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
                 content_path: str = "/Users/tashi/Desktop/projects/whatsup/reddit_data.json",
                 theme_path: str = "/Users/tashi/Desktop/projects/whatsup/topic_recommendations.json"):
        self.client = OpenAI()
        self.content_path = content_path
        self.theme_path = theme_path
        self.system_message = """
You are a summarizer AI designed to integrate important discussion topics (and only important) across a Reddit subreddit about AI for **a technical, detail oriented engineer audience**. 
    
Your task is to create a unified summary that captures key points, conversations, and references without being channel-specific. Focus on thematic coherence and group similar discussion points, even if they are from different posts.

You are going to summarize the specific post that you will be given. You will be given the post body now; respond with a 2-3 sentence summary, formatted in markdown by bolding notable names, terms, facts, dates, and numbers. No acknowledgement needed, only respond with the summary. Do not talk about "showcasing" or "highlighting" anything in the summary; stick to pure facts and opinions expressed by the post author, stated in the post body.

Summaries should be succinct (2 sentences each), and should include any relevant info with specific numbers, key names and links/urls discussed (do not hallucinate your own quotes or links). If none were given, just don't say anything. If insufficient context was provided, omit it from the summary. Use markdown syntax to format links, preferably [link title](https://link.url), and format in **bold** the key words and key headlines, and *italicize* direct quotes.USE ACTIVE VOICE, NOT PASSIVE VOICE. Resist bland corporate language like "underscore" and "leverage" and "fostering innovation", and significantly reduce usage of words like in the following list.

<style>
    You can use technical jargon for an average AI Engineer audience who has been following along for a while.
    But you should consider alternatives if you use these overused words from the ### overused list ###. 
    
    ### overused list ###
    Hurdles, Bustling, Harnessing, Unveiling the power, Realm, Depicted, Demistify, 
    Insurmountable, New Era, Poised, Unravel, Entanglement, Unprecedented, Eerie connection, 
    Beacon, Unleash, Delve, Enrich, Multifaced, Elevate, Discover, Supercharge, Unlock, 
    Unleash, Tailored, Elegant, Delve, Dive, Ever-evolving, Realm, Meticulously, Grappling, 
    Weighing, Picture, Architect, Adventure, J      ourney, Embark, Navigate, Navigation
    ### overused list ###
</style>
        """
    
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
                model="gpt-4o-mini",
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
            
    def save_summary_to_json(self, summary_data: Dict[str, Any], output_path: str = "theme_summaries.json") -> None:
        """
        Save the theme summary data to a JSON file.
        
        Args:
            summary_data: Dictionary containing theme, post IDs, and summary
            output_path: Path to save the JSON file (default: theme_summaries.json)
        """
        import json
        import os
        
        try:
            # Load existing summaries if file exists
            existing_summaries = []
            if os.path.exists(output_path):
                with open(output_path, 'r') as f:
                    existing_summaries = json.load(f)
                    
            # Add new summary
            existing_summaries.append(summary_data)
            
            # Save updated summaries
            with open(output_path, 'w') as f:
                json.dump(existing_summaries, indent=2, ensure_ascii=False, fp=f)
                
        except Exception as e:
            print(f"Error saving summary to JSON: {str(e)}")
            raise

if __name__ == "__main__":
    summarizer = PostSummarizer()
    summary = summarizer.summarize_theme_posts(2)
