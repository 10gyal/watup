import os
from dotenv import load_dotenv
import praw
from typing import Optional

class RedditAuth:
    """
    A class to handle Reddit API authentication and provide a configured PRAW instance.
    """
    
    def __init__(self):
        """Initialize the RedditAuth instance by loading environment variables."""
        load_dotenv()
        self.client_id = os.getenv('REDDIT_CLIENT_ID')
        self.client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        self.username = os.getenv('REDDIT_USERNAME')
        self.password = os.getenv('REDDIT_PASSWORD')
        self.user_agent = 'script:whatsup:v1.0 (by /u/{})'.format(self.username) if self.username else None
        self._reddit: Optional[praw.Reddit] = None

    def validate_credentials(self) -> bool:
        """
        Validate that all required credentials are present.
        
        Returns:
            bool: True if all credentials are present, False otherwise
        """
        required_vars = [
            ('Client ID', self.client_id),
            ('Client Secret', self.client_secret),
            ('Username', self.username),
            ('Password', self.password)
        ]
        
        missing = [name for name, value in required_vars if not value]
        
        if missing:
            print(f"Missing required credentials: {', '.join(missing)}")
            return False
        return True

    def authenticate(self) -> Optional[praw.Reddit]:
        """
        Authenticate with Reddit using the provided credentials.
        
        Returns:
            praw.Reddit: Authenticated Reddit instance if successful, None otherwise
        
        Raises:
            Exception: If authentication fails
        """
        if not self.validate_credentials():
            return None

        try:
            self._reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                username=self.username,
                password=self.password,
                user_agent=self.user_agent
            )
            # Verify the authentication worked
            self._reddit.user.me()
            print("-" * 100) 
            print("Successfully authenticated with Reddit!")
            return self._reddit
        except Exception as e:
            print(f"Authentication failed: {str(e)}")
            return None

    @property
    def reddit(self) -> Optional[praw.Reddit]:
        """
        Get the authenticated Reddit instance.
        
        Returns:
            praw.Reddit: Authenticated Reddit instance if available, None otherwise
        """
        if not self._reddit:
            return self.authenticate()
        return self._reddit

def get_reddit_instance() -> Optional[praw.Reddit]:
    """
    Helper function to get an authenticated Reddit instance.
    
    Returns:
        praw.Reddit: Authenticated Reddit instance if successful, None otherwise
    """
    auth = RedditAuth()
    return auth.reddit

if __name__ == "__main__":
    # Example usage
    reddit = get_reddit_instance()
    if reddit:
        print(f"Authenticated as: {reddit.user.me()}")
        print("-" * 100)