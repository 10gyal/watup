import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any

class RedditDB:
    def __init__(self, db_path: str = "reddit_data.db"):
        """Initialize database connection and create tables if they don't exist."""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        # Enable JSON support
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.create_tables()

    def create_tables(self):
        """Create necessary tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reddit_searches (
            id TEXT PRIMARY KEY,
            keyword TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            subreddit JSON NOT NULL
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS subreddit_posts (
            id TEXT PRIMARY KEY,
            post_id TEXT NOT NULL,
            subreddit_search_id TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            post_data JSON NOT NULL,
            FOREIGN KEY (subreddit_search_id) REFERENCES reddit_searches(id),
            UNIQUE(post_id, subreddit_search_id)
        )
        ''')
        
        self.conn.commit()

    def record_search(self, keyword: str, results: List[Dict[str, Any]]) -> List[str]:
        """
        Record search results in the database.
        
        Args:
            keyword (str): The search term used
            results (List[Dict[str, Any]]): List of raw subreddit results
            
        Returns:
            List[str]: List of generated search IDs
        """
        cursor = self.conn.cursor()
        search_ids = []
        
        for result in results:
            search_id = str(uuid.uuid4())
            cursor.execute('''
            INSERT INTO reddit_searches (id, keyword, created_at, subreddit)
            VALUES (?, ?, ?, ?)
            ''', (
                search_id,
                keyword,
                datetime.now().isoformat(),
                json.dumps(result)
            ))
            search_ids.append(search_id)
        
        self.conn.commit()
        return search_ids

    def record_posts(self, subreddit_search_id: str, posts: List[Dict[str, Any]]) -> None:
        """
        Record posts for a subreddit search result.
        
        Args:
            subreddit_search_id (str): ID of the related reddit_searches record
            posts (List[Dict]): List of posts to store
        """
        cursor = self.conn.cursor()
        
        for post in posts:
            try:
                cursor.execute('''
                INSERT INTO subreddit_posts (id, post_id, subreddit_search_id, created_at, post_data)
                VALUES (?, ?, ?, ?, ?)
                ''', (
                    str(uuid.uuid4()),
                    post['id'],
                    subreddit_search_id,
                    datetime.now().isoformat(),
                    json.dumps(post)
                ))
            except sqlite3.IntegrityError:
                # Skip if this post already exists for this subreddit search
                continue
        
        self.conn.commit()

    def get_recent_searches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent search results.
        
        Args:
            limit (int): Number of recent results to return
            
        Returns:
            List[Dict[str, Any]]: List of recent search results with their posts
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
        SELECT 
            s.id, s.keyword, s.created_at, s.subreddit,
            p.post_data
        FROM reddit_searches s
        LEFT JOIN subreddit_posts p ON s.id = p.subreddit_search_id
        ORDER BY s.created_at DESC, p.created_at DESC
        ''')
        
        searches = {}
        for row in cursor.fetchall():
            search_id = row[0]
            if search_id not in searches:
                searches[search_id] = {
                    'id': row[0],
                    'keyword': row[1],
                    'created_at': row[2],
                    'subreddit': json.loads(row[3]),
                    'posts': []
                }
            if row[4]:  # If there are posts
                searches[search_id]['posts'].append(json.loads(row[4]))
        
        return list(searches.values())[:limit]

    def close(self):
        """Close the database connection."""
        self.conn.close()
