#!/usr/bin/env python3
"""
AI News API - Fetches news from RSS feeds and serves them via a Flask API
"""
import feedparser
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request, send_from_directory, make_response
from flask_cors import CORS
from datetime import datetime
import random
import logging
import time
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Add logging middleware for requests
@app.before_request
def log_request_info():
    logger.info('Request Headers: %s', request.headers)
    logger.info('Request Method: %s, Path: %s', request.method, request.path)

# List of AI-related RSS feeds
RSS_FEEDS = [
    {
        'url': 'https://techcrunch.com/category/artificial-intelligence/feed/',
        'name': 'TechCrunch',
        'website': 'https://techcrunch.com',
        'logo': 'https://techcrunch.com/wp-content/uploads/2021/01/TechCrunch_logo.png'
    },
    {
        'url': 'https://venturebeat.com/category/ai/feed/',
        'name': 'VentureBeat',
        'website': 'https://venturebeat.com',
        'logo': 'https://venturebeat.com/wp-content/uploads/2018/09/venturebeat-logo-rec.png?w=192'
    },
    {
        'url': 'https://www.wired.com/feed/tag/ai/latest/rss',
        'name': 'Wired',
        'website': 'https://www.wired.com',
        'logo': 'https://www.wired.com/assets/logo-header.png'
    }
]

# Fallback images if no image is found in the feed
FALLBACK_IMAGES = [
    'https://images.unsplash.com/photo-1677442135046-c10d516d84c6?q=100&w=2000&auto=format&fit=crop',
    'https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?q=100&w=2000&auto=format&fit=crop',
    'https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?q=100&w=2000&auto=format&fit=crop',
    'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?q=100&w=2000&auto=format&fit=crop'
]

# Cache for articles to reduce repeated parsing
# Initialize the articles cache with empty values
articles_cache = {
    'articles': [],
    'last_updated': None
}
CACHE_TIMEOUT = 3600  # 1 hour in seconds

def parse_rss_feeds():
    """Parse multiple RSS feeds and extract article information"""
    logger.info("Starting to parse RSS feeds...")
    all_articles = []
    
    for feed_source in RSS_FEEDS:
        try:
            logger.info(f"Parsing feed: {feed_source['url']}")
            feed = feedparser.parse(feed_source['url'])
            
            for entry in feed.entries[:5]:  # Limit to 5 articles per feed
                # Extract article details
                article = {
                    'id': random.randint(1000, 9999),
                    'title': entry.get('title', 'Untitled Article'),
                    'summary': _extract_summary(entry),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', datetime.now().isoformat()),
                    'image': get_article_image(entry),
                    'source': {
                        'name': feed_source['name'],
                        'url': feed_source['website'],
                        'logo': feed_source['logo']
                    },
                    'isHero': False
                }
                
                # Set the first article as hero
                if len(all_articles) == 0:
                    article['isHero'] = True
                
                all_articles.append(article)
            
            logger.info(f"Successfully parsed {len(feed.entries[:5])} articles from {feed_source['name']}")
            
        except Exception as e:
            logger.error(f"Error parsing feed {feed_source['url']}: {e}")
    
    logger.info(f"Total articles parsed: {len(all_articles)}")
    return all_articles

def _extract_summary(entry):
    """Extract and clean up article summary"""
    summary = ""
    
    # Try to get summary from different feed formats
    if hasattr(entry, 'summary'):
        summary = entry.summary
    elif hasattr(entry, 'description'):
        summary = entry.description
    
    # Clean up HTML from summary
    if summary:
        soup = BeautifulSoup(summary, 'html.parser')
        summary = soup.get_text().strip()
        
        # Limit summary length
        if len(summary) > 200:
            summary = summary[:197] + "..."
    else:
        summary = "Click to read the full article."
        
    return summary

def extract_first_paragraph(html_content, max_words=50):
    """Extract first paragraph from HTML content, limited to max_words"""
    if not html_content:
        return ""
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove any script or style elements
    for script in soup(["script", "style"]):
        script.extract()
    
    # Find the first paragraph
    paragraph = soup.find('p')
    if paragraph:
        text = paragraph.get_text().strip()
    else:
        # If no paragraph, just get the text
        text = soup.get_text().strip()
    
    # Clean up the text
    text = clean_text(text)
    
    # Split into words and limit to max_words
    words = text.split()
    if len(words) > max_words:
        text = ' '.join(words[:max_words]) + '...'
    
    return text

def clean_text(text):
    """Clean up text by removing unusual characters and fixing encoding issues"""
    if not text:
        return ""
    
    # Replace common HTML entities and Unicode characters
    replacements = {
        '&nbsp;': ' ',
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&apos;': "'",
        '\u2019': "'",  # Right single quotation mark
        '\u2018': "'",  # Left single quotation mark
        '\u201c': '"',  # Left double quotation mark
        '\u201d': '"',  # Right double quotation mark
        '\u2014': '-',  # Em dash
        '\u2013': '-',  # En dash
        '\u00a0': ' ',  # Non-breaking space
    }
    
    for old, new in replacements.items():
        if old in text:
            text = text.replace(old, new)
    
    # Normalize whitespace
    import re
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def is_ai_related(entry, keywords):
    """Check if entry is related to AI based on keywords"""
    try:
        if not keywords:
            # If no keywords provided, include all articles
            return True
            
        # Convert all content to lowercase for case-insensitive matching
        title = entry.title.lower() if hasattr(entry, 'title') else ''
        summary = ''
        
        if hasattr(entry, 'summary'):
            summary = entry.summary.lower()
        elif hasattr(entry, 'description'):
            summary = entry.description.lower()
            
        # Check if any keyword is in title or summary
        for keyword in keywords:
            if keyword.lower() in title or keyword.lower() in summary:
                return True
                
        return False
    except Exception as e:
        logger.error(f"Error in is_ai_related: {str(e)}")
        return False

def get_article_image(entry):
    """Extract image URL from feed entry"""
    try:
        # Method 1: Check for media_thumbnail
        if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
            return entry.media_thumbnail[0]['url']
            
        # Method 2: Check for media content
        if hasattr(entry, 'media_content') and entry.media_content:
            for media in entry.media_content:
                if media.get('type', '').startswith('image/'):
                    return media['url']
                # Some feeds don't specify type but still contain image URLs
                if 'url' in media and (media['url'].endswith('.jpg') or 
                                      media['url'].endswith('.jpeg') or 
                                      media['url'].endswith('.png')):  
                    return media['url']
        
        # Method 3: Check for enclosures
        if hasattr(entry, 'enclosures') and entry.enclosures:
            for enclosure in entry.enclosures:
                if enclosure.get('type', '').startswith('image/'):
                    return enclosure.get('href', enclosure.get('url', ''))
        
        # Method 4: Check for content field
        if hasattr(entry, 'content') and entry.content:
            for content in entry.content:
                if 'value' in content:
                    soup = BeautifulSoup(content['value'], 'html.parser')
                    img = soup.find('img')
                    if img and img.get('src'):
                        # Avoid small icons and tracking pixels
                        if not (img.get('width') and int(img['width']) < 50) and not \
                           (img.get('height') and int(img['height']) < 50):
                            # Make sure we're not grabbing an icon or tiny image
                            if not any(word in img['src'].lower() for word in ['icon', 'logo', 'avatar', 'button', 'pixel', 'tracking']):
                                return img['src']
        
        # Method 5: Parse HTML in summary
        if hasattr(entry, 'summary'):
            soup = BeautifulSoup(entry.summary, 'html.parser')
            imgs = soup.find_all('img')
            for img in imgs:
                # Avoid small icons and tracking pixels by checking src and dimensions
                if img.get('src'):
                    # Skip probable logos/icons
                    if not (img.get('width') and int(img['width']) < 50) and not \
                       (img.get('height') and int(img['height']) < 50):
                        # Make sure we're not grabbing an icon or tiny image
                        if not any(word in img['src'].lower() for word in ['icon', 'logo', 'avatar', 'button', 'pixel', 'tracking']):
                            return img['src']
        
        # Method 6: Fetch the full article to look for images (optimized for performance)
        try:
            # Only attempt this for entries where we couldn't find images
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(entry.link, headers=headers, timeout=3)  # 3-second timeout to not slow down the app
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # First look for Open Graph image meta tag (most accurate for article image)
                og_image = soup.find('meta', property='og:image')
                if og_image and og_image.get('content'):
                    return og_image['content']
                
                # Then look for Twitter image card
                twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
                if twitter_image and twitter_image.get('content'):
                    return twitter_image['content']
                
                # Finally look for article-specific images
                article_tag = soup.find('article') or soup.find('main') or soup
                imgs = article_tag.find_all('img')
                for img in imgs:
                    if img.get('src') and not any(word in img['src'].lower() for word in ['icon', 'logo', 'avatar', 'button', 'pixel', 'tracking']):
                        if img.get('width') and int(img['width']) >= 200 or img.get('height') and int(img['height']) >= 200:
                            # Found a reasonably sized image
                            src = img['src']
                            # Fix relative URLs
                            if src.startswith('//'):
                                src = 'https:' + src
                            elif src.startswith('/'):
                                # Extract domain from entry link
                                from urllib.parse import urlparse
                                domain = '{uri.scheme}://{uri.netloc}'.format(uri=urlparse(entry.link))
                                src = domain + src
                            return src
        except Exception as e:
            logger.info(f"Couldn't extract image from article content: {e}")
        
        # If all else fails, fallback to random image
        fallback = random.choice(FALLBACK_IMAGES)
        logger.info(f"Using fallback image for {entry.get('title', 'Unknown title')}: {fallback}")
        return fallback
    except Exception as e:
        logger.error(f"Error extracting image: {e}")
        return random.choice(FALLBACK_IMAGES)
    
    # Check summary/description
    summary = entry.get('summary', '').lower()
    for keyword in keywords:
        if keyword.lower() in summary:
            return True
    
    # Check categories/tags
    if 'tags' in entry:
        for tag in entry.tags:
            tag_name = tag.get('term', '').lower()
            for keyword in keywords:
                if keyword.lower() in tag_name:
                    return True
    
    return False

# Define fallback images to use when no image is found
FALLBACK_IMAGES = [
    "https://images.unsplash.com/photo-1677442135046-c10d516d84c6?q=100&w=2000&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?q=100&w=2000&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?q=100&w=2000&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?q=100&w=2000&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?q=100&w=2000&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1616469829581-73993eb86b02?q=100&w=2000&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1557838429-06a189a5cb26?q=100&w=2000&auto=format&fit=crop",
]

def fetch_article_from_source(source, max_articles=5):
    """Fetch and parse RSS feed from a given source"""
    try:
        feed = feedparser.parse(source['url'])
        articles = []
        
        count = 0
        for entry in feed.entries:
            # Only process if AI-related or if this source has AI-specific feed
            ai_keywords = ['ai', 'artificial intelligence', 'machine learning', 'deep learning', 'neural network', 'gpt', 'llm']
            if 'ai' in source['url'].lower() or is_ai_related(entry, ai_keywords):
                # Try to get the published date
                published = entry.get('published_parsed')
                if published:
                    published_date = datetime(*published[:6]).isoformat()
                else:
                    published_date = datetime.now().isoformat()
                
                # Extract summary
                if 'summary' in entry:
                    summary = extract_first_paragraph(entry.summary, 50)
                elif 'description' in entry:
                    summary = extract_first_paragraph(entry.description, 50)
                else:
                    summary = "Read the full article for more information."
                    
                # Clean the title to remove any artifacts
                title = clean_text(entry.title)
                
                # Get image URL or use a fallback image
                try:
                    image_url = get_article_image(entry)
                except Exception as e:
                    logger.error(f"Error getting image: {str(e)}")
                    image_url = random.choice(FALLBACK_IMAGES)
                
                # Create article object
                article = {
                    'id': hash(entry.link) % 100000,  # Generate a simple hash as ID
                    'title': entry.title,  # We'll clean the title directly in the code
                    'summary': summary,
                    'link': entry.link,
                    'published': published_date,
                    'image': image_url,
                    'source': {
                        'name': source['name'],
                        'website': source.get('website', ''),
                        'logo': source.get('logo', '')
                    }
                }
                
                articles.append(article)
                count += 1
                
                if count >= max_articles:
                    break
                    
        return articles
    except Exception as e:
        logger.error(f"Error fetching from {source['name']}: {str(e)}")
        return []

def fetch_all_articles():
    """Fetch articles from all sources and update the cache"""
    all_articles = []
    
    for source in RSS_FEEDS:
        articles = fetch_article_from_source(source)
        all_articles.extend(articles)
    
    # Sort by published date (newest first)
    all_articles.sort(key=lambda x: x.get('published', ''), reverse=True)
    
    # Designate the newest article as the hero
    if all_articles:
        all_articles[0]['isHero'] = True
    
    # Update cache
    articles_cache['articles'] = all_articles
    articles_cache['last_updated'] = datetime.now()
    
    logger.info(f"Fetched {len(all_articles)} articles from {len(RSS_FEEDS)} sources")
    return all_articles

def background_fetcher():
    """Background thread to update the article cache periodically"""
    while True:
        try:
            fetch_all_articles()
            # Update every 30 minutes
            time.sleep(1800)
        except Exception as e:
            logger.error(f"Error in background fetcher: {str(e)}")
            # If there's an error, try again in 5 minutes
            time.sleep(300)

@app.route('/')
def index():
    """Serve the main page"""
    return app.send_static_file('index.html')

@app.route('/test')
def test_endpoint():
    """Simple test endpoint that just returns text"""
    return "Test endpoint working!"

@app.route('/api/summary')
def api_summary():
    """Generate a text summary of all articles"""
    try:
        # Current date for the file
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Create the text content
        summary_text = f"NexusAI News Summary - {current_date}\n"
        summary_text += "=" * 50 + "\n\n"
        
        # Use existing articles without refreshing cache to avoid errors
        if articles_cache['articles']:
            # Find a hero article (first article or one marked as hero)
            hero_article = None
            for article in articles_cache['articles']:
                if article.get('isHero'):
                    hero_article = article
                    break
            
            # If no hero found, use the first article
            if not hero_article and articles_cache['articles']:
                hero_article = articles_cache['articles'][0]
            
            # Add hero article
            if hero_article:
                summary_text += f"HEADLINE: {hero_article['title']}\n"
                summary_text += f"SOURCE: {hero_article['source']['name']}\n"
                summary_text += f"LINK: {hero_article['link']}\n\n"
            
            # Add other articles
            summary_text += "OTHER STORIES:\n" + "-" * 50 + "\n\n"
            
            for article in articles_cache['articles']:
                # Skip the hero article if we found one
                if hero_article and article == hero_article:
                    continue
                
                summary_text += f"TITLE: {article['title']}\n"
                summary_text += f"SOURCE: {article['source']['name']}\n"
                summary_text += f"LINK: {article['link']}\n\n"
        else:
            summary_text += "No articles available at this time.\n\n"
        
        # Add footer
        summary_text += "=" * 50 + "\n"
        summary_text += f"Generated by NexusAI News Hub on {current_date}\n"
        
        # Set response headers to make it a downloadable file
        response = make_response(summary_text)
        response.headers["Content-Disposition"] = f"attachment; filename=nexusai_news_summary_{current_date}.txt"
        response.headers["Content-Type"] = "text/plain"
        
        return response
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        return jsonify({"error": "An error occurred while generating the summary"}), 500

@app.route('/api/articles')
def api_articles():
    """API endpoint to get articles"""
    # Check if cache needs refreshing (older than 30 minutes or empty)
    if (articles_cache['last_updated'] is None or 
        (datetime.now() - articles_cache['last_updated']).seconds > 1800 or
        not articles_cache['articles']):
        fetch_all_articles()
    
    # Get optional limit parameter
    limit = request.args.get('limit', default=10, type=int)
    
    # Return cached articles with limit
    return jsonify({
        'articles': articles_cache['articles'][:limit],
        'total': len(articles_cache['articles']),
        'lastUpdated': articles_cache['last_updated'].isoformat() if articles_cache['last_updated'] else None
    })

@app.route('/api/hero')
def get_hero_article():
    """API endpoint to get only the hero article"""
    # Check if cache needs refreshing
    if (articles_cache['last_updated'] is None or 
        (datetime.now() - articles_cache['last_updated']).seconds > 1800 or
        not articles_cache['articles']):
        fetch_all_articles()
    
    # Find hero article
    hero = next((article for article in articles_cache['articles'] if article.get('isHero')), None)
    
    if not hero and articles_cache['articles']:
        # If no hero is designated but we have articles, use the first one
        hero = articles_cache['articles'][0]
        hero['isHero'] = True
    
    return jsonify({
        'article': hero,
        'lastUpdated': articles_cache['last_updated'].isoformat() if articles_cache['last_updated'] else None
    })

if __name__ == '__main__':
    # Set the port, use 5001 if not specified
    port = int(os.environ.get('PORT', 5001))
    
    # Initial fetch of articles
    CACHED_ARTICLES = parse_rss_feeds()
    LAST_UPDATED = time.time()
    
    logger.info(f"Starting API server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
