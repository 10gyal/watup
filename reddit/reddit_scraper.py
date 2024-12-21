import json
from typing import List, Dict, Any
from auth import get_reddit_instance
import praw
from datetime import datetime

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

def count_data_stats(results: Dict[str, List[Dict[str, Any]]]) -> Dict[str, int]:
    """
    Count the number of posts, comments, and replies in the scraped data.
    
    Args:
        results (Dict[str, List[Dict]]): Scraped Reddit data
        
    Returns:
        Dict[str, int]: Statistics about the data
    """
    total_posts = 0
    total_comments = 0
    total_replies = 0
    
    def count_replies(comment: Dict[str, Any]) -> int:
        replies_count = len(comment.get('replies', []))
        for reply in comment.get('replies', []):
            replies_count += count_replies(reply)
        return replies_count
    
    for subreddit, posts in results.items():
        total_posts += len(posts)
        for post in posts:
            comments = post.get('comments', [])
            total_comments += len(comments)
            for comment in comments:
                total_replies += count_replies(comment)
    
    return {
        'posts': total_posts,
        'comments': total_comments,
        'replies': total_replies
    }

def format_comment_tree(comment: Dict[str, Any], indent: int = 2) -> str:
    """
    Helper function to format a comment and its replies in a tree structure.
    
    Args:
        comment (Dict[str, Any]): Comment data dictionary
        indent (int): Current indentation level
        
    Returns:
        str: Formatted comment tree as text
    """
    indent_str = " " * indent
    output = [
        f"\n{indent_str}└─ {comment['body']}",
        f"{indent_str}   Score: {comment['score']} | Author: {comment['author']}"
    ]
    
    # Format replies recursively
    for reply in comment.get('replies', []):
        output.append(format_comment_tree(reply, indent + 4))
    
    return "\n".join(output)

def format_reddit_data(results: Dict[str, List[Dict[str, Any]]], api_requests: int) -> str:
    """
    Format the scraped Reddit data as a readable text string.
    
    Args:
        results (Dict[str, List[Dict]]): Scraped Reddit data
        
    Returns:
        str: Formatted data as text
    """
    output = []
    stats = count_data_stats(results)
    
    # Add timestamp and statistics header
    print(f"=== Reddit Data Scrape - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    print(f"Total Posts: {stats['posts']}")
    print(f"Total Comments: {stats['comments']}")
    print(f"Total Replies: {stats['replies']}")
    print(f"Total API Requests: {api_requests}")
    print("\n" + "=" * 80 + "\n")
    
    # Format the data
    for subreddit, posts in results.items():
        output.append(f"\nTop posts from r/{subreddit}:")
        output.append("-" * 80)
        
        for i, post in enumerate(posts, 1):
            output.extend([
                f"\n{i}. {post['title']}",
                f"Score: {post['score']} | Comments: {post['num_comments']}",
                f"URL: {post['url']}",
                "\nComment thread:"
            ])
            
            for comment in post['comments']:
                output.append(format_comment_tree(comment))
            
            output.append("-" * 80)
    
    return "\n".join(output)

def format_json_data(results: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Format the scraped Reddit data into a simplified JSON structure.
    
    Args:
        results (Dict[str, List[Dict]]): Scraped Reddit data
        
    Returns:
        List[Dict]: List of formatted posts with comments
    """
    formatted_posts = []
    
    for subreddit, posts in results.items():
        for post in posts:
            # Format comments using the same tree structure as the text format
            comments_text = []
            for comment in post.get('comments', []):
                comments_text.append(format_comment_tree(comment))
            
            # Create the formatted post entry
            formatted_post = {
                'post_id': post['id'],
                'post_content': post['selftext'] if post['selftext'] else post['title'],
                'post_url': post['url'],
                'score': post['score'],
                'author': post['author'],
                'created_utc': post['created_utc'],
                'num_comments': post['num_comments'],
                'subreddit': subreddit,
                'comments': '\n'.join(comments_text)
            }
            formatted_posts.append(formatted_post)
    
    return formatted_posts

def save_to_file(data: str, filename: str):
    """
    Save formatted data to a text file.
    
    Args:
        data (str): Formatted data to save
        filename (str): Name of the file to save to
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(data)
        print(f"Data successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving data to file: {str(e)}")

def save_json_to_file(data: List[Dict[str, Any]], filename: str):
    """
    Save data as JSON file.
    
    Args:
        data (List[Dict]): Data to save
        filename (str): Name of the file to save to
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"JSON data successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving JSON data to file: {str(e)}")

def main():
    """
    Main function to demonstrate usage of the RedditScraper class.
    """
    scraper = RedditScraper()
    results = scraper.scrape_all_subreddits()
    
    # Save formatted text data
    formatted_data = format_reddit_data(results, scraper.api_requests)
    save_to_file(formatted_data, 'reddit_data.txt')
    
    # Save JSON data
    json_data = format_json_data(results)
    save_json_to_file(json_data, 'reddit_data.json')

if __name__ == "__main__":
    main()
