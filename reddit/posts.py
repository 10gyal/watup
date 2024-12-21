from typing import List, Dict, Any, Optional
from datetime import datetime
import praw
from auth import get_reddit_instance

def get_subreddit_posts(subreddit_name: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch top posts from a subreddit for the last 24 hours.
    
    Args:
        subreddit_name (str): Name of the subreddit to fetch posts from
        limit (int): Maximum number of posts to fetch
        
    Returns:
        List[Dict[str, Any]]: List of top posts
    """
    reddit = get_reddit_instance()
    if not reddit:
        print(f"Failed to authenticate with Reddit while fetching posts for r/{subreddit_name}")
        return []
    
    posts = []
    try:
        subreddit = reddit.subreddit(subreddit_name)
        
        # Get top posts from the last 24 hours
        for post in subreddit.top(time_filter='day', limit=limit):
            post_data = {
                'id': post.id,
                'title': post.title,
                'score': post.score,
                'url': post.url,
                'created_utc': post.created_utc,
                'num_comments': post.num_comments,
                'author': str(post.author),
                'permalink': post.permalink,
                'is_self': post.is_self,
                'selftext': post.selftext if post.is_self else None,
                'upvote_ratio': post.upvote_ratio,
                'stickied': post.stickied,
                'over_18': post.over_18,
                'spoiler': post.spoiler,
                'link_flair_text': post.link_flair_text
            }
            posts.append(post_data)
                
    except Exception as e:
        print(f"Error fetching posts from r/{subreddit_name}: {str(e)}")
    
    return posts

def format_post_for_display(post: Dict[str, Any]) -> str:
    """Format a post for console display."""
    created_time = post['created_utc'].fromtimestamp(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    is_informative = post.get('is_informative')
    informative_status = f"[INFORMATIVE]" if is_informative else "[NOT INFORMATIVE]" if is_informative is not None else ""
    
    return (
        f"Title: {post['title']} {informative_status}\n"
        f"Score: {post['score']:,} (ratio: {post['upvote_ratio']:.2%})\n"
        f"Comments: {post['num_comments']:,}\n"
        f"Posted: {created_time}\n"
        f"Author: u/{post['author']}\n"
        f"URL: https://reddit.com{post['permalink']}\n"
        + (f"Content: {post['selftext']}\n" if post.get('selftext') else "")
    )

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch top posts from a subreddit')
    parser.add_argument('subreddit', help='Subreddit name to fetch posts from')
    parser.add_argument('--limit', type=int, default=5, help='Number of posts to fetch (default: 5)')
    
    args = parser.parse_args()
    
    posts = get_subreddit_posts(args.subreddit, args.limit)
    
    if posts:
        print(f"\nTop posts from r/{args.subreddit} in the last 24 hours:")
        for post in posts:
            print("\n" + "="*80)
            print(format_post_for_display(post))
    else:
        print(f"\nNo posts found or an error occurred.")
