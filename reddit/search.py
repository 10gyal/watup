import praw
import argparse
import json
from typing import List, Dict, Optional, Tuple
from .auth import get_reddit_instance
from .utils import load_config
from openai import OpenAI
from pydantic import BaseModel, Field

class SubredditResult(BaseModel):
    name: str
    description: str
    subscribers: int
    relevance_score: float

class KeywordsResponse(BaseModel):
    query_keywords: List[str] = Field(..., description="List of keywords to search for relevant subreddits.")


def get_query_keywords() -> List[str]:
    """Get keywords based on user profile to search for relevant subreddits."""
    user_profile = load_config()["user_profile"]
    client = OpenAI()

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a Reddit expert. Your task is to generate a list of keywords to search for relevant subreddits. You will be given a user profile and asked to generate a list of keywords based on the user's interests and intent."},
            {"role": "user", "content": str(user_profile)},
        ],
        response_format=KeywordsResponse,
    )
    
    response = response.choices[0].message.parsed.model_dump()
    return response["query_keywords"]

def search_subreddit(reddit: praw.Reddit, keyword: str) -> List[SubredditResult]:
    """
    Search for subreddits using a keyword and return relevant results.
    
    Args:
        reddit: Authenticated Reddit instance
        keyword: Keyword to search for
        
    Returns:
        List of SubredditResult objects containing relevant subreddits
    """
    results = []
    try:
        # Search for subreddits using the keyword
        for subreddit in reddit.subreddits.search(keyword, limit=5):
            # Calculate a simple relevance score based on subscriber count and keyword presence
            relevance_score = min(subreddit.subscribers / 1000000, 1.0)  # Normalize by 1M subscribers
            if keyword.lower() in subreddit.display_name.lower():
                relevance_score += 0.3
            if keyword.lower() in (subreddit.public_description or "").lower():
                relevance_score += 0.2
                
            results.append(SubredditResult(
                name=subreddit.display_name,
                description=subreddit.public_description or "No description available",
                subscribers=subreddit.subscribers,
                relevance_score=round(relevance_score, 2)
            ))
    except Exception as e:
        print(f"Error searching for subreddit with keyword '{keyword}': {str(e)}")
    
    # Sort by relevance score
    return sorted(results, key=lambda x: x.relevance_score, reverse=True)

def get_popular_subreddits(keywords: Optional[List[str]] = None) -> Dict[str, List[SubredditResult]]:
    """
    Get popular subreddits based on provided keywords or user profile.
    
    Args:
        keywords: Optional list of keywords to search for. If None, gets keywords from user profile.
        
    Returns:
        Dictionary mapping keywords to lists of relevant subreddits
    """
    # Get Reddit instance
    reddit = get_reddit_instance()
    if not reddit:
        print("Failed to authenticate with Reddit")
        return {}
        
    # Get keywords if not provided
    if keywords is None:
        keywords = get_query_keywords()
    
    # Search for subreddits for each keyword
    results = {}
    for keyword in keywords:
        subreddits = search_subreddit(reddit, keyword)
        if subreddits:
            results[keyword] = subreddits
            
    return results

def format_subreddit_results(results: Dict[str, List[SubredditResult]]) -> str:
    """
    Format subreddit search results into a readable string.
    
    Args:
        results: Dictionary of keyword to subreddit results
        
    Returns:
        Formatted string of results
    """
    output = []
    for keyword, subreddits in results.items():
        output.append(f"\nResults for keyword: {keyword}")
        output.append("-" * 80)
        
        for sr in subreddits:
            output.append(f"\nr/{sr.name} ({sr.subscribers:,} subscribers)")
            output.append(f"Relevance Score: {sr.relevance_score}")
            output.append(f"Description: {sr.description[:200]}...")
            
    return "\n".join(output)

if __name__ == "__main__":
    # Example usage
    results = get_popular_subreddits()
    print(format_subreddit_results(results))
