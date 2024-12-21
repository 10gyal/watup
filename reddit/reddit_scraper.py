import json
from typing import List, Dict, Any
from auth import get_reddit_instance
import praw

class RedditScraper:
    """
    A class to scrape top posts and comments from specified subreddits.
    """
    
    def __init__(self, config_file: str = 'reddit/config.json'):
        """
        Initialize the RedditScraper with path to the config JSON file.
        
        Args:
            config_file (str): Path to the configuration JSON file
        """
        self.config_file = config_file
        self.api_requests = 0  # Counter for API requests
        self.reddit = get_reddit_instance()
        if not self.reddit:
            raise Exception("Failed to authenticate with Reddit")
        
        # Load configuration
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                self.config = config['scraping']
                self.subreddits = config['subreddits']
        except Exception as e:
            print(f"Error loading config file: {str(e)}")
            self.config = {
                "posts_limit": 5,
                "comments_limit": 5,
                "replies_limit": 5,
                "comment_depth": 5,
                "time_filter": "day"
            }
            self.subreddits = []

    def get_subreddits(self) -> List[str]:
        """
        Get the list of subreddits from config.
        
        Returns:
            List[str]: List of subreddit names
        """
        return self.subreddits

    def get_top_posts(self, subreddit_name: str, limit: int = None) -> List[Dict[str, Any]]:
        """
        Get top posts from a subreddit.
        
        Args:
            subreddit_name (str): Name of the subreddit
            limit (int, optional): Number of top posts to fetch. If None, uses config value.
            
        Returns:
            List[Dict]: List of post information dictionaries
        """
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            posts = []
            
            limit = limit if limit is not None else self.config['posts_limit']
            self.api_requests += 1  # Count subreddit.top request
            for post in subreddit.top(limit=limit, time_filter=self.config['time_filter']):
                post_data = {
                    'id': post.id,
                    'title': post.title,
                    'url': post.url,
                    'score': post.score,
                    'created_utc': post.created_utc,
                    'author': str(post.author),
                    'num_comments': post.num_comments,
                    'permalink': post.permalink,
                    'selftext': post.selftext,
                    'comments': self.get_top_comments(post)
                }
                posts.append(post_data)
            
            return posts
        except Exception as e:
            print(f"Error fetching posts from r/{subreddit_name}: {str(e)}")
            return []

    def get_comment_replies(self, comment: praw.models.Comment, depth: int = None) -> List[Dict[str, Any]]:
        """
        Recursively get replies to a comment up to a specified depth.
        
        Args:
            comment (praw.models.Comment): Reddit comment object
            depth (int, optional): Maximum depth of replies to fetch. If None, uses config value.
            
        Returns:
            List[Dict]: List of reply information dictionaries
        """
        depth = depth if depth is not None else self.config['comment_depth']
        if depth <= 0:
            return []
            
        try:
            replies = []
            self.api_requests += 1  # Count comment.refresh request
            comment.refresh()  # Ensure we have the latest replies
            for reply in comment.replies[:self.config['replies_limit']]:
                reply_data = {
                    'id': reply.id,
                    'author': str(reply.author),
                    'body': reply.body,
                    'score': reply.score,
                    'created_utc': reply.created_utc,
                    'replies': self.get_comment_replies(reply, depth - 1)  # Recursive call
                }
                replies.append(reply_data)
            return replies
        except Exception as e:
            print(f"Error fetching replies for comment {comment.id}: {str(e)}")
            return []

    def get_top_comments(self, post: praw.models.Submission, limit: int = None) -> List[Dict[str, Any]]:
        """
        Get top comments from a post, including their replies.
        
        Args:
            post (praw.models.Submission): Reddit post object
            limit (int): Number of top comments to fetch
            
        Returns:
            List[Dict]: List of comment information dictionaries with replies
        """
        try:
            self.api_requests += 1  # Count replace_more request
            post.comments.replace_more(limit=0)  # Remove "load more comments" items
            comments = []
            
            limit = limit if limit is not None else self.config['comments_limit']
            for comment in post.comments[:limit]:
                comment_data = {
                    'id': comment.id,
                    'author': str(comment.author),
                    'body': comment.body,
                    'score': comment.score,
                    'created_utc': comment.created_utc,
                    'replies': self.get_comment_replies(comment)  # Get replies for each top comment
                }
                comments.append(comment_data)
            
            return comments
        except Exception as e:
            print(f"Error fetching comments for post {post.id}: {str(e)}")
            return []

    def scrape_all_subreddits(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Scrape top posts and comments from all subreddits in the JSON file.
        Uses configuration values for limits.
        
        Returns:
            Dict[str, List[Dict]]: Dictionary mapping subreddit names to their posts
        """
        subreddits = self.get_subreddits()
        results = {}
        
        for subreddit in subreddits:
            print(f"Scraping r/{subreddit}...")
            posts = self.get_top_posts(subreddit)
            results[subreddit] = posts
            
        return results
