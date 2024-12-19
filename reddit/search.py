import praw
import argparse
import json
from typing import List, Dict, Optional
from auth import get_reddit_instance
from db import RedditDB
from posts import get_subreddit_posts, format_post_for_display

def load_subreddits_from_file(file_path: str) -> Optional[List[Dict[str, str]]]:
    """
    Load subreddit information from a JSON file.
    
    Args:
        file_path (str): Path to the JSON file containing subreddit names
        
    Returns:
        Optional[List[Dict[str, str]]]: List of dictionaries containing subreddit information,
                                      or None if loading/authentication fails
    """
    reddit = get_reddit_instance()
    if not reddit:
        print("Failed to authenticate with Reddit. Please check your credentials.")
        return None
    
    try:
        with open(file_path, 'r') as f:
            subreddit_names = json.load(f)
        
        if not isinstance(subreddit_names, list):
            print("Error: JSON file must contain a list of subreddit names")
            return None
            
        subreddits = []
        for name in subreddit_names:
            try:
                subreddit = reddit.subreddit(name)
                # Store complete subreddit data
                subreddit_data = {
                    'display_name': subreddit.display_name,
                    'title': subreddit.title,
                    'subscribers': subreddit.subscribers,
                    'public_description': subreddit.public_description,
                    'created_utc': subreddit.created_utc,
                    'over18': subreddit.over18,
                    'subscribers': subreddit.subscribers,
                    'subreddit_type': subreddit.subreddit_type,
                    'url': subreddit.url,
                    'active_user_count': getattr(subreddit, 'active_user_count', None)
                }
                subreddits.append(subreddit_data)
            except Exception as e:
                print(f"Error loading subreddit {name}: {str(e)}")
                continue
                
        return subreddits
    except Exception as e:
        print(f"Error loading subreddits from file: {str(e)}")
        return None

def search_subreddits(keyword: str, limit: int = 5, save_to_db: bool = True) -> Optional[List[Dict[str, str]]]:
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
            # Store complete subreddit data
            subreddit_data = {
                'display_name': subreddit.display_name,
                'title': subreddit.title,
                'subscribers': subreddit.subscribers,
                'public_description': subreddit.public_description,
                'created_utc': subreddit.created_utc,
                'over18': subreddit.over18,
                'subscribers': subreddit.subscribers,
                'subreddit_type': subreddit.subreddit_type,
                'url': subreddit.url,
                'active_user_count': getattr(subreddit, 'active_user_count', None)
            }
            subreddits.append(subreddit_data)
            
        # Save results and fetch posts if requested
        if save_to_db and subreddits:
            try:
                db = RedditDB()
                search_ids = db.record_search(keyword, subreddits)
                
                # Fetch and store top posts for each subreddit
                print("\nFetching top posts from each subreddit...")
                for subreddit, search_id in zip(subreddits, search_ids):
                    print(f"\nFetching posts from r/{subreddit['display_name']}...")
                    posts = get_subreddit_posts(subreddit['display_name'], limit=5)
                    if posts:
                        db.record_posts(search_id, posts)
                    
                db.close()
            except Exception as e:
                print(f"Error saving to database: {str(e)}")
        
        return subreddits
    except Exception as e:
        print(f"Error searching subreddits: {str(e)}")
        return None

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Find or load subreddits and their posts')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--keyword', help='Keyword to search for subreddits')
    group.add_argument('--file', help='JSON file containing list of subreddit names')
    parser.add_argument('--limit', type=int, default=2, help='Number of search results to return (default: 2)')
    parser.add_argument('--no-save', action='store_true', help='Do not save results to database')
    parser.add_argument('--show-posts', action='store_true', help='Show posts from each subreddit')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Get subreddits either through search or from file
    if args.keyword:
        results = search_subreddits(args.keyword, args.limit, not args.no_save)
    else:
        results = load_subreddits_from_file(args.file)
        if results and not args.no_save:
            # Save the manually loaded subreddits
            try:
                db = RedditDB()
                search_ids = db.record_search("manual_load", results)
                
                # Fetch and store top posts for each subreddit
                print("\nFetching top posts from each subreddit...")
                for subreddit, search_id in zip(results, search_ids):
                    print(f"\nFetching posts from r/{subreddit['display_name']}...")
                    posts = get_subreddit_posts(subreddit['display_name'], limit=5)
                    if posts:
                        db.record_posts(search_id, posts)
                    
                db.close()
            except Exception as e:
                print(f"Error saving to database: {str(e)}")
    
    if results:
        # Print results
        print(f"\nTop {len(results)} subreddits for '{args.keyword}':\n")
        for i, subreddit in enumerate(results, 1):
            print(f"{i}. r/{subreddit['display_name']}")
            print(f"   Title: {subreddit['title']}")
            print(f"   Subscribers: {subreddit['subscribers']:,}")
            description = subreddit['public_description']
            print(f"   Description: {description[:200] + '...' if len(description) > 200 else description}\n")
            
            if args.show_posts:
                posts = get_subreddit_posts(subreddit['display_name'], limit=5)
                if posts:
                    print("   Top posts from the last 24 hours:")
                    for post in posts:
                        print("\n   " + "-"*76)
                        print("   " + format_post_for_display(post).replace("\n", "\n   "))
    else:
        print("\nNo results found or an error occurred.")

if __name__ == '__main__':
    main()
