# Reddit Data Processing System

This directory contains a comprehensive system for scraping, analyzing, and processing Reddit data with a focus on AI-related subreddits. The system is modular and consists of several specialized components.

## Core Components

### Data Collection
- `reddit_scraper.py`: Core scraping engine that fetches posts and comments from configured subreddits
- `auth.py`: Handles Reddit API authentication
- `config.json`: Configuration file for subreddits to monitor and scraping parameters

### Data Processing
- `post_summarizer.py`: Processes and summarizes Reddit posts
- `comment_summarizer.py`: Analyzes and summarizes comment threads
- `topic_rec.py`: Generates topic recommendations based on collected data
- `search.py`: Implements search functionality across collected Reddit data

### Data Management
- `db.py`: Database operations for storing Reddit data
- `formatter.py`: Formats scraped data into different output formats
- `utils.py`: Utility functions used across the system

### Main Entry Point
- `main.py`: Orchestrates the entire data collection and processing pipeline

## Configuration

The system is configured through `config.json` which specifies:
- Target subreddits (currently focused on AI-related communities)
- Scraping parameters:
  - Number of posts to fetch
  - Comment depth
  - Time filter for posts
  - Limits for comments and replies

## Data Flow

1. The system authenticates with Reddit's API
2. Scrapes configured subreddits for posts and comments
3. Stores data in both JSON format and a database
4. Processes the collected data to generate:
   - Post summaries
   - Comment analysis
   - Topic recommendations

## Output Files

The system generates several output files:
- `reddit_data.json`: Raw scraped data
- `post_summary.md`: Summarized post content
- `topic_recommendations.json`: Generated topic recommendations
- `theme_summaries.json`: Thematic analysis of content

## Usage

The system is designed to be run through the main.py entry point, which coordinates the entire data collection and processing pipeline. It handles:
- Initializing the scraper
- Collecting data from configured subreddits
- Processing and formatting the data
- Generating recommendations and summaries

This modular architecture allows for easy extension and modification of individual components while maintaining a clear separation of concerns between data collection, processing, and analysis functions.

## Installation & Setup

1. Install required dependencies:
```bash
pip install praw pandas numpy
```

2. Set up Reddit API credentials in environment variables:
```bash
export REDDIT_CLIENT_ID="your_client_id"
export REDDIT_CLIENT_SECRET="your_client_secret"
export REDDIT_USER_AGENT="your_user_agent"
```

3. Initialize the database:
```bash
python -c "from reddit.db import RedditDB; RedditDB('reddit_data.db').initialize()"
```

## Example Usage

```python
from reddit.reddit_scraper import RedditScraper
from reddit.topic_rec import TopicRecommender

# Initialize scraper
scraper = RedditScraper()

# Scrape data
results = scraper.scrape_all_subreddits()

# Generate topic recommendations
recommender = TopicRecommender('reddit_data.json')
topics = recommender.recommend_topics()
```

## Error Handling & Troubleshooting

Common issues and solutions:

1. API Authentication Errors
   - Verify environment variables are set correctly
   - Check Reddit API credentials
   - Ensure user agent follows Reddit's guidelines

2. Rate Limiting
   - The system implements automatic rate limiting
   - Default: 60 requests per minute
   - Adjust timing in utils.py if needed

3. Database Errors
   - Ensure proper permissions on database directory
   - Check database connection string
   - Verify schema initialization

## API Rate Limiting

The system implements Reddit's API guidelines:
- Maximum 60 requests per minute
- Automatic cooldown when limit is reached
- Request counting in RedditScraper class
- Built-in delay between requests

## Development Guidelines

For contributors:

1. Code Style
   - Follow PEP 8 guidelines
   - Use type hints
   - Document all functions and classes

2. Testing
   - Write unit tests for new features
   - Run existing test suite before submitting changes
   - Mock Reddit API calls in tests

3. Pull Request Process
   - Create feature branch
   - Update documentation
   - Add tests
   - Request review

4. Architecture Guidelines
   - Maintain modularity
   - Follow single responsibility principle
   - Document dependencies
   - Handle errors gracefully
