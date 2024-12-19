import praw
import argparse
from typing import List, Dict, Optional
from auth import get_reddit_instance

def search_subreddits(keyword: str, limit: int = 5) -> Optional[List[Dict[str, str]]]:
    """
    Search for subreddits matching the given keyword and return top results.
    
    Args:
        keyword (str): Search term to find relevant subreddits
        limit (int): Number of results to return (default: 5)
        
    Returns:
        Optional[List[Dict[str, str]]]: List of dictionaries containing subreddit information,
                                      or None if authentication fails
    """
    reddit = get_reddit_instance()
    if not reddit:
        print("Failed to authenticate with Reddit. Please check your credentials.")
        return None
    
    # Search for subreddits
    subreddits = []
    try:
        for subreddit in reddit.subreddits.search(keyword, limit=limit):
            subreddits.append({
                'name': subreddit.display_name,
                'title': subreddit.title,
                'subscribers': f"{subreddit.subscribers:,}",
                'description': subreddit.public_description[:200] + '...' if len(subreddit.public_description) > 200 else subreddit.public_description
            })
        return subreddits
    except Exception as e:
        print(f"Error searching subreddits: {str(e)}")
        return None

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Find top subreddits for a given search term')
    parser.add_argument('keyword', help='Keyword to search for subreddits')
    parser.add_argument('--limit', type=int, default=2, help='Number of results to return (default: 2)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Search for subreddits
    results = search_subreddits(args.keyword, args.limit)
    
    if results:
        # Print results
        print(f"\nTop {len(results)} subreddits for '{args.keyword}':\n")
        for i, subreddit in enumerate(results, 1):
            print(f"{i}. r/{subreddit['name']}")
            print(f"   Title: {subreddit['title']}")
            print(f"   Subscribers: {subreddit['subscribers']}")
            print(f"   Description: {subreddit['description']}\n")
    else:
        print("\nNo results found or an error occurred.")

if __name__ == '__main__':
    main()
