from .utils import load_config
from .reddit_scraper import RedditScraper
from .sys_prompt_generator import SystemPromptGenerator
from .prompts.examples.topic_recommender_prompt import SYSTEM_MESSAGE as TOPIC_RECOMMENDER_MESSAGE
from .prompts.examples.post_summarizer_prompt import SYSTEM_MESSAGE as POST_SUMMARIZER_MESSAGE
from .prompts.examples.comment_summarizer_prompt import SYSTEM_MESSAGE as COMMENT_SUMMARIZER_MESSAGE
from .formatter import (
    format_reddit_data,
    format_json_data,
    save_to_file,
    save_json_to_file
)
from .topic_rec import TopicRecommender
from .post_summarizer import PostSummarizer
from .comment_summarizer import CommentSummarizer

def main():
    """
    Main function to demonstrate usage of the RedditScraper class
    and formatting utilities.
    """
    # Load configuration
    config = load_config()
    paths = config["paths"]
    
    # Generate system prompts
    topic_generator = SystemPromptGenerator(TOPIC_RECOMMENDER_MESSAGE)
    post_generator = SystemPromptGenerator(POST_SUMMARIZER_MESSAGE)
    comment_generator = SystemPromptGenerator(COMMENT_SUMMARIZER_MESSAGE)
    
    topic_prompt = topic_generator.generate_prompt(save_as="topic_recommender_prompt.txt")
    post_prompt = post_generator.generate_prompt(save_as="post_summarizer_prompt.txt")
    comment_prompt = comment_generator.generate_prompt(save_as="comment_summarizer_prompt.txt")
    
    # Initialize and run the scraper
    scraper = RedditScraper()
    results = scraper.scrape_all_subreddits()
    
    # Save formatted text data
    formatted_data = format_reddit_data(results, scraper.api_requests)
    save_to_file(formatted_data, paths["reddit_data_txt"])
    
    # Save JSON data
    json_data = format_json_data(results)
    save_json_to_file(json_data, paths["reddit_data_json"])
    
    # Get topic recommendations
    topic_recommender = TopicRecommender(paths["reddit_data_json"])
    topics = topic_recommender.recommend_topics()
    
    # Save topic recommendations
    save_json_to_file(topics, paths["topic_recommendations"])
    
    # Generate post summaries for each theme
    post_summarizer = PostSummarizer(
        content_path=paths["reddit_data_json"],
        theme_path=paths["topic_recommendations"]
    )
    
    # Clear existing theme summaries to avoid duplicates
    import os
    if os.path.exists(paths["theme_summaries"]):
        os.remove(paths["theme_summaries"])
    
    # Generate summaries for all themes
    themes = topics.get("themes", [])
    print(f"Processing {len(themes)} themes...")
    for theme_index in range(len(themes)):
        try:
            theme = themes[theme_index]
            print(f"Summarizing theme {theme_index + 1}/{len(themes)}: {theme['theme']}")
            post_summarizer.summarize_theme_posts(theme_index)
        except Exception as e:
            print(f"Error summarizing theme {theme_index}: {str(e)}")
            continue
            
    # Generate comment summaries for each theme
    comment_summarizer = CommentSummarizer(
        summaries_path=paths["theme_summaries"],
        output_path=paths["comment_summaries"]
    )
    comment_summarizer.summarize_comments()

if __name__ == "__main__":
    main()
