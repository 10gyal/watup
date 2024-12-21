import json
from typing import Dict, List, Any
from datetime import datetime

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
