from pydantic import BaseModel, Field
from typing import List, Dict, Any
from openai import OpenAI
from .posts import DailyPosts, Posts, Post
from dotenv import load_dotenv

load_dotenv()

PATH = "/Users/tashi/Desktop/projects/whatsup/reddit_data.json"

system_message = """
You are a summarizer AI designed to integrate important discussion topics (and only important) across a Reddit subreddit about AI for **a technical, detail oriented engineer audience**. 
    
Your task is to create a unified summary that captures key points, conversations, and references without being channel-specific. Focus on thematic coherence and group similar discussion points, even if they are from different posts.

You are going to summarize the specific post that you will be given. You will be given the post body now; respond with a 2-3 sentence summary, formatted in markdown by bolding notable names, terms, facts, dates, and numbers. No acknowledgement needed, only respond with the summary. Do not talk about "showcasing" or "highlighting" anything in the summary; stick to pure facts and opinions expressed by the post author, stated in the post body.

Summaries should be succinct (2 sentences each), and should include any relevant info with specific numbers, key names and links/urls discussed (do not hallucinate your own quotes or links). If none were given, just don't say anything. If insufficient context was provided, omit it from the summary. Use markdown syntax to format links, preferably [link title](https://link.url), and format in **bold** the key words and key headlines, and *italicize* direct quotes.USE ACTIVE VOICE, NOT PASSIVE VOICE. Resist bland corporate language like "underscore" and "leverage" and "fostering innovation", and significantly reduce usage of words like in the following list.

<style>
    You can use technical jargon for an average AI Engineer audience who has been following along for a while.
    But you should consider alternatives if you use these overused words from the ### overused list ###. 
    
    ### overused list ###
    Hurdles, Bustling, Harnessing, Unveiling the power, Realm, Depicted, Demistify, 
    Insurmountable, New Era, Poised, Unravel, Entanglement, Unprecedented, Eerie connection, 
    Beacon, Unleash, Delve, Enrich, Multifaced, Elevate, Discover, Supercharge, Unlock, 
    Unleash, Tailored, Elegant, Delve, Dive, Ever-evolving, Realm, Meticulously, Grappling, 
    Weighing, Picture, Architect, Adventure, Journey, Embark, Navigate, Navigation
    ### overused list ###
</style>
"""

class Summary(BaseModel):
    response: str = Field(..., description="Summary of the post content")


class PostSummary:
    def __init__(self):
        self.client = OpenAI()
    
    def summarize(self, post):
        """
        Summarize the post content
        """
        response = self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": post},
            ],
            response_format=Summary,
        )
        response = response.choices[0].message.parsed
        response = response.model_dump()

        return response
    


if __name__ == "__main__":
    posts = Posts(PATH).get_posts()
    post = posts[0].content
    print(post)
    summary = PostSummary().summarize(post)
    print(summary)
