"""
given a user profile, search for relevant subreddits based on keywords
"""


import praw
import argparse
import json
from typing import List, Dict, Optional, Tuple
from openai import OpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from .auth import get_reddit_instance


load_dotenv()


class Keywords(BaseModel):
    keywords: List[str] = Field(..., description="Keywords extracted from the user profile")

def extract_keywords(user_profile: str):
    """
    Extract keywords from user profile
    """
    system_message = """
    You are an intelligent assistant tasked with generating relevant keywords based on a user's profile. The user's profile contains information about their background (who they are) and their goals or interests (their intent). Your role is to infer and identify key concepts, even if they are not explicitly mentioned in the profile, and provide a list of keywords that can be used to search for subreddits matching their interests.

    - Focus on understanding the user's profile context to form a comprehensive and relevant list of keywords.
    - Include related and inferred concepts that align with the user's interests, goals, and potential areas of exploration.

    Example Workflow:
    1. Analyze the profile:
    - Who: Aspiring UX designer.
    - Intent: I want to learn about AI use in Figma Design.
    
    2. Infer and Extract Keywords:
    - UX design, AI, Figma, design tools, collaborative design, generative design, prototyping tools, AI-assisted workflows.

    Be creative and accurate in your keyword generation, ensuring they align closely with the user’s profile and intent while covering related concepts that may be valuable.
    """

    client = OpenAI()
    response = client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content":system_message},
                    {"role": "user", "content": user_profile},
                ],
                response_format=Keywords,
            )
    
    response = response.choices[0].message.parsed.model_dump()
    return response["keywords"]


def search_subreddits(keywords: List[str]) -> Dict[str, List[Dict]]:
    """
    Search for relevant subreddits based on keywords coming from extract_keywords()
    
    Args:
        keywords (List[str]): List of keywords to search for
        
    Returns:
        Dict[str, List[Dict]]: Dictionary mapping keywords to lists of subreddit information
        Example:
        {
            "keyword1": [
                {
                    "name": "subreddit_name",
                    "description": "subreddit description",
                    "subscribers": 1000,
                    "url": "subreddit_url"
                },
                ...
            ],
            ...
        }
    """
    
    reddit = get_reddit_instance()
    if not reddit:
        raise Exception("Failed to authenticate with Reddit")
    
    results = {}
    
    for keyword in keywords:
        subreddits = []
        # Search for subreddits related to the keyword
        for subreddit in reddit.subreddits.search(keyword, limit=5):
            try:
                subreddit_info = {
                    "name": subreddit.display_name,
                    "description": subreddit.description,
                    "subscribers": subreddit.subscribers,
                    "url": f"https://reddit.com/r/{subreddit.display_name}"
                }
                subreddits.append(subreddit_info)
            except Exception as e:
                print(f"Error processing subreddit {subreddit.display_name}: {str(e)}")
                continue
        
        results[keyword] = subreddits
    
    return results

def check_relevancy():
    """
    For each of the top 5 subreddits from each keyword, get the subreddit description, get top 5 posts of the month, get top 2 comments for each post.
    Evaluate if the subreddit is relevant to user profile based on the posts and comments.
    For each subreddit, true if relevant, false otherwise.
    """

    pass

def get_relevant_subreddits():
    """
    Get all the relevant subreddits i.e where "relevancy" is true
    """

    pass

if __name__ == "__main__":
    user_profile = """user_profile":{
        "who": "Aspiring ux designer.",
        "intent": "I want to learn about AI use in Figma Design"
    }"""
    kws = extract_keywords(user_profile)
    print("Extracted Keywords:", kws)
    
    # Search for subreddits based on keywords
    try:
        subreddit_results = search_subreddits(kws)
        print("\nFound Subreddits:")
        for keyword, subreddits in subreddit_results.items():
            print(f"\nKeyword: {keyword}")
            for subreddit in subreddits:
                print(f"- r/{subreddit['name']}: {subreddit['subscribers']} subscribers")
    except Exception as e:
        print(f"Error searching subreddits: {str(e)}")
