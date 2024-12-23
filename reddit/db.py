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
        
        # Create tables with proper schema
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
            subreddit TEXT NOT NULL,
            title TEXT,
            url TEXT,
            score INTEGER,
            created_utc REAL,
            author TEXT,
            num_comments INTEGER,
            permalink TEXT,
            selftext TEXT,
            comments TEXT,
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
                INSERT INTO subreddit_posts (
                    id, post_id, subreddit_search_id, subreddit, title, url,
                    score, created_utc, author, num_comments,
                    permalink, selftext, comments
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(uuid.uuid4()),
                    post['id'],
                    subreddit_search_id,
                    post.get('subreddit', ''),
                    post.get('title', ''),
                    post.get('url', ''),
                    post.get('score', 0),
                    post.get('created_utc', 0.0),
                    post.get('author', ''),
                    post.get('num_comments', 0),
                    post.get('permalink', ''),
                    post.get('selftext', ''),
                    json.dumps(post.get('comments', []))
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
            p.post_id, p.subreddit, p.title, p.url, p.score, p.created_utc,
            p.author, p.num_comments, p.permalink, p.selftext, p.comments
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
                post_data = {
                    'id': row[4],
                    'subreddit': row[5],
                    'title': row[6],
                    'url': row[7],
                    'score': row[8],
                    'created_utc': row[9],
                    'author': row[10],
                    'num_comments': row[11],
                    'permalink': row[12],
                    'selftext': row[13],
                    'comments': json.loads(row[14])
                }
                searches[search_id]['posts'].append(post_data)
        
        return list(searches.values())[:limit]

    def drop_tables(self):
        """Drop all tables from the database."""
        cursor = self.conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS subreddit_posts")
        cursor.execute("DROP TABLE IF EXISTS reddit_searches")
        self.conn.commit()

    def close(self):
        """Close the database connection."""
        self.conn.close()
