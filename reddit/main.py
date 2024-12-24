from .reddit_scraper import RedditScraper
from .formatter import (
    format_reddit_data,
    format_json_data,
    save_to_file,
    save_json_to_file
)
from .topic_rec import TopicRecommender

def main():
    """
    Main function to demonstrate usage of the RedditScraper class
    and formatting utilities.
    """
    # Initialize and run the scraper
    scraper = RedditScraper()
    results = scraper.scrape_all_subreddits()
    
    # Save formatted text data
    formatted_data = format_reddit_data(results, scraper.api_requests)
    save_to_file(formatted_data, 'reddit_data.txt')
    
    # Save JSON data
    json_data = format_json_data(results)
    path_file = 'reddit_data.json'
    save_json_to_file(json_data, path_file)
    
    # Get topic recommendations
    topic_recommender = TopicRecommender(path_file)
    topics = topic_recommender.recommend_topics()
    
    # Save topic recommendations
    save_json_to_file(topics, 'topic_recommendations.json')

if __name__ == "__main__":
    main()
