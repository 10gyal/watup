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
                    "description": subreddit.public_description,
                    "subscribers": subreddit.subscribers,
                    "url": f"https://reddit.com/r/{subreddit.display_name}"
                }
                subreddits.append(subreddit_info)
            except Exception as e:
                print(f"Error processing subreddit {subreddit.display_name}: {str(e)}")
                continue
        
        results[keyword] = subreddits
    
    return results

class Relevancy(BaseModel):
    relevancy: bool = Field(..., description="Whether the subreddit is relevant to the user profile")

def get_relevant_subreddits(user_profile: str, subreddit_results: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
    """
    Filter subreddits based on relevancy to user profile
    
    Args:
        user_profile (str): User profile containing background and intent
        subreddit_results (Dict[str, List[Dict]]): Results from search_subreddits()
        
    Returns:
        Dict[str, List[Dict]]: Dictionary containing only relevant subreddits
    """
    system_message = """
    You are an intelligent assistant tasked with determining whether a subreddit matches a given user profile. You will be provided with the following inputs:
    1. The user's profile, including their background (who they are) and goals or interests (their intent).
    2. The subreddit's name and description.

    Your role is to analyze the provided inputs and assess whether the subreddit could potentially bring any value to the user based on their profile. Consider the user's background, interests, and intent to determine the relevance of the subreddit.

    - Focus on understanding the user's profile and the context of the subreddit.
    - Evaluate the subreddit name and description for alignment with the user's interests and goals.
    - Provide a boolean output:
    - `True` if the subreddit is relevant to the user's profile.
    - `False` if the subreddit is not relevant to the user's profile.

    Your output must only be `True` or `False`, based on the relevance of the subreddit to the user's profile. Avoid any additional explanations in the output.
    """

    relevant_results = {}
    
    for keyword, subreddits in subreddit_results.items():
        relevant_subreddits = []
        
        for subreddit in subreddits:
            subreddit_detail = {
                "name": subreddit["name"],
                "description": subreddit["description"],
                "subscribers": subreddit["subscribers"]
            }
            
            user_message = f"User Profile: {user_profile}\n\nSubreddit Details: {subreddit_detail}"

            client = OpenAI()
            response = client.beta.chat.completions.parse(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content":system_message},
                            {"role": "user", "content": user_message},
                        ],
                        response_format=Relevancy,
                    )
            
            response = response.choices[0].message.parsed.model_dump()
            
            print(f"\nAnalyzing r/{subreddit['name']}...")
            print(f"Relevancy: {'✓ Relevant' if response['relevancy'] else '✗ Not relevant'}")
            
            if response["relevancy"]:
                relevant_subreddits.append(subreddit)
        
        if relevant_subreddits:
            relevant_results[keyword] = relevant_subreddits
    
    return relevant_results

if __name__ == "__main__":
    user_profile = """user_profile":{
        "who": "Aspiring ux designer.",
        "intent": "I want to learn about AI use in Figma Design"
    }"""
    
    # Step 1: Extract keywords
    kws = extract_keywords(user_profile)
    print("Extracted Keywords:", kws)
    
    try:
        # Step 2: Search for subreddits
        subreddit_results = search_subreddits(kws)
        print("\nFound Subreddits:")
        for keyword, subreddits in subreddit_results.items():
            print(f"\nKeyword: {keyword}")
            for subreddit in subreddits:
                print(f"- r/{subreddit['name']}: {subreddit['subscribers']} subscribers")
                print(f"  Description: {subreddit['description']}")
        
        # Step 3: Filter and show relevant subreddits
        print("\nFiltering relevant subreddits...")
        relevant_results = get_relevant_subreddits(user_profile, subreddit_results)
        
        # Print relevant results
        for keyword, subreddits in relevant_results.items():
            print(f"\nRelevant subreddits for keyword: {keyword}")
            for subreddit in subreddits:
                print(f"\nr/{subreddit['name']}:")
                print(f"Description: {subreddit['description']}")
                print(f"Subscribers: {subreddit['subscribers']}")


    except Exception as e:
        print(f"Error: {str(e)}")
