from pydantic import BaseModel, Field
from typing import List, Dict, Any
from openai import AsyncOpenAI
from dotenv import load_dotenv
import asyncio
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

class IsInformative(BaseModel):
    is_informative: bool = Field(..., description="Whether the post is informative or not")

client = AsyncOpenAI()

async def analyze_post_content(post_content: str) -> bool:
    """Analyze a single post's content to determine if it's informative."""
    try:
        response = await client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant who is an expert at determining if a post is informative to a user who is an active member of the AI community."},
                {"role": "user", "content": post_content},
            ],
            response_format=IsInformative,
        )
        
        response = response.choices[0].message.parsed
        response = response.model_dump()
        is_informative = response.get("is_informative", False)
        print(f"Post content analyzed. is_informative: {is_informative}")
        return is_informative
        
    except Exception as e:
        print(f"Error analyzing post: {e}")
        return False

async def process_batch(posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process a batch of posts concurrently.
    
    Args:
        posts: List of posts to analyze
        
    Returns:
        List of posts with is_informative field added
    """
    tasks = []
    for post in posts:
        task = asyncio.create_task(
            analyze_post_content(post["selftext"])
            if "selftext" in post and post["selftext"]
            else asyncio.sleep(0)
        )
        tasks.append(task)
    
    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update posts with results, handling any exceptions
        for post, result in zip(posts, results):
            is_informative = (
                isinstance(result, bool) and result
                if "selftext" in post and post["selftext"]
                else False
            )
            post["is_informative"] = is_informative
            print(f"Post {post['id']} is_informative set to: {is_informative}")
            
    except Exception as e:
        print(f"Error processing batch: {e}")
        # Mark all posts as not informative in case of batch processing error
        for post in posts:
            post["is_informative"] = False
    
    return posts

async def filter_posts(posts: List[Dict[str, Any]], batch_size: int = 5) -> List[Dict[str, Any]]:
    """
    Filter posts based on their selftext content using async batching.
    
    Args:
        posts: List of posts to analyze
        batch_size: Number of posts to process concurrently
        
    Returns:
        List of posts with is_informative field added
    """
    if not posts:
        return []
        
    batches = [posts[i:i + batch_size] for i in range(0, len(posts), batch_size)]
    tasks = [process_batch(batch) for batch in batches]
    
    try:
        processed_batches = await asyncio.gather(*tasks)
        return [post for batch in processed_batches for post in batch]
    except Exception as e:
        print(f"Error in filter_posts: {e}")
        # Return original posts marked as not informative in case of error
        for post in posts:
            post["is_informative"] = False
        return posts

def get_informative_posts(
    posts: List[Dict[str, Any]], 
    batch_size: int = 5
) -> List[Dict[str, Any]]:
    """
    Synchronous wrapper for async filter_posts function.
    
    Args:
        posts: List of posts to analyze
        batch_size: Number of posts to process concurrently. Must be positive.
        
    Returns:
        List of posts with is_informative field added
    
    Raises:
        ValueError: If batch_size is less than 1
    """
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")
        
    if not posts:
        return []
        
    return asyncio.run(filter_posts(posts, batch_size))
