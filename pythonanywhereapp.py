#!/usr/bin/env python3
"""
All-in-one Flask application for NexusAI News Hub
- Serves static files (HTML, CSS, JS)
- Provides API endpoints for news articles
- Fetches articles from RSS feeds
"""
import feedparser
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from datetime import datetime
import random
import logging
import time
import os
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Get the directory of this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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

# Sample data to use as fallback
SAMPLE_ARTICLES = [
    {
        'id': 1,
        'title': "OpenAI Unveils GPT-5 with Unprecedented Multimodal Capabilities",
        'summary': "The latest model from OpenAI shows remarkable improvements in reasoning, visual understanding, and code generation, setting new benchmarks across all major AI evaluation metrics.",
        'image': "https://images.unsplash.com/photo-1677442135046-c10d516d84c6?q=80&w=1932&auto=format&fit=crop",
        'source': {
            'name': 'TechCrunch',
            'url': 'https://techcrunch.com',
            'logo': 'https://techcrunch.com/wp-content/uploads/2015/02/cropped-cropped-favicon-gradient.png'
        },
        'link': "https://techcrunch.com/ai/openai-gpt5-announcement",
        'isHero': True
    },
    {
        'id': 2,
        'title': "EU Passes Comprehensive AI Regulation Framework",
        'summary': "The European Union has finalized its AI Act, establishing the world's most stringent rules for artificial intelligence development and deployment.",
        'image': "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?q=80&w=1770&auto=format&fit=crop",
        'source': {
            'name': 'MIT Technology Review',
            'url': 'https://www.technologyreview.com',
            'logo': 'https://www.technologyreview.com/favicon.ico'
        },
        'link': "https://www.technologyreview.com/europe-ai-act-regulation"
    },
    {
        'id': 3,
        'title': "Google DeepMind's AlphaFold 3 Makes Breakthrough in Protein Structure Prediction",
        'summary': "The latest iteration of AlphaFold can now predict protein interactions and small molecule binding with unprecedented accuracy.",
        'image': "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?q=80&w=1770&auto=format&fit=crop",
        'source': {
            'name': 'Wired',
            'url': 'https://www.wired.com',
            'logo': 'https://www.wired.com/favicon.ico'
        },
        'link': "https://www.wired.com/google-deepmind-alphafold3"
    }
]

# Cache for articles to reduce repeated parsing
CACHED_ARTICLES = []
LAST_UPDATED = None
CACHE_TIMEOUT = 3600  # 1 hour in seconds
CACHE_FILE = os.path.join(BASE_DIR, 'articles_cache.json')

def load_cached_articles():
    """Load articles from cache file if it exists"""
    global CACHED_ARTICLES, LAST_UPDATED
    
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
                CACHED_ARTICLES = cache_data.get('articles', [])
                LAST_UPDATED = cache_data.get('timestamp')
                logger.info(f"Loaded {len(CACHED_ARTICLES)} articles from cache file")
    except Exception as e:
        logger.error(f"Error loading cache file: {e}")
        # Fall back to sample data
        CACHED_ARTICLES = SAMPLE_ARTICLES
        LAST_UPDATED = time.time()

def save_cached_articles():
    """Save articles to cache file"""
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump({
                'articles': CACHED_ARTICLES,
                'timestamp': LAST_UPDATED
            }, f)
        logger.info(f"Saved {len(CACHED_ARTICLES)} articles to cache file")
    except Exception as e:
        logger.error(f"Error saving cache file: {e}")

def parse_rss_feeds():
    """Parse multiple RSS feeds and extract article information"""
    logger.info("Starting to parse RSS feeds...")
    all_articles = []
    
    try:
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
                        'image': _extract_image(entry),
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
    except Exception as e:
        logger.error(f"Error in parse_rss_feeds: {e}")
        # Return sample data if something goes wrong
        return SAMPLE_ARTICLES
    
    if not all_articles:
        logger.warning("No articles parsed from feeds, falling back to sample data")
        return SAMPLE_ARTICLES
    
    logger.info(f"Total articles parsed: {len(all_articles)}")
    return all_articles

def _extract_summary(entry):
    """Extract and clean up article summary"""
    # Try different fields that might contain the summary
    if 'summary' in entry:
        text = entry.summary
    elif 'description' in entry:
        text = entry.description
    else:
        return "No summary available"
    
    # Clean up HTML
    try:
        soup = BeautifulSoup(text, 'html.parser')
        # Remove script and style elements
        for tag in soup(['script', 'style']):
            tag.decompose()
        
        # Get text and clean it up
        text = soup.get_text().strip()
        # Normalize whitespace
        text = ' '.join(text.split())
        
        # Limit length
        if len(text) > 200:
            text = text[:197] + '...'
        
        return text
    except:
        return "Summary extraction failed"

def _extract_image(entry):
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

def get_articles(force_refresh=False):
    """Get articles, refreshing the cache if needed"""
    global CACHED_ARTICLES, LAST_UPDATED
    
    # Check if cache is empty or expired
    current_time = time.time()
    if force_refresh or not CACHED_ARTICLES or not LAST_UPDATED or (current_time - LAST_UPDATED > CACHE_TIMEOUT):
        logger.info("Cache empty or expired, fetching new articles")
        try:
            CACHED_ARTICLES = parse_rss_feeds()
            LAST_UPDATED = current_time
            save_cached_articles()
        except Exception as e:
            logger.error(f"Error refreshing articles: {e}")
            if not CACHED_ARTICLES:
                CACHED_ARTICLES = SAMPLE_ARTICLES
    
    return CACHED_ARTICLES

# Routes for static files
@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/test')
def test_endpoint():
    """Simple test endpoint that just returns text"""
    return "Test endpoint working!"

@app.route('/<path:path>')
def static_files(path):
    """Serve static files like CSS, JS, images"""
    return send_from_directory(BASE_DIR, path)

# API routes
@app.route('/api/summary')
def api_summary():
    """Generate a text summary of all articles"""
    try:
        # Current date for the file
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Create the text content
        summary_text = f"NexusAI News Summary - {current_date}\n"
        summary_text += "=" * 50 + "\n\n"
        
        # Get all articles
        articles = get_articles()
        
        if articles:
            # Find a hero article (first article or one marked as hero)
            hero_article = None
            for article in articles:
                if article.get('isHero'):
                    hero_article = article
                    break
            
            # If no hero found, use the first article
            if not hero_article and articles:
                hero_article = articles[0]
            
            # Add hero article
            if hero_article:
                summary_text += f"HEADLINE: {hero_article['title']}\n"
                summary_text += f"SOURCE: {hero_article['source']['name']}\n"
                summary_text += f"LINK: {hero_article['link']}\n\n"
            
            # Add other articles
            summary_text += "OTHER STORIES:\n" + "-" * 50 + "\n\n"
            
            for article in articles:
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
        from flask import make_response
        response = make_response(summary_text)
        response.headers["Content-Disposition"] = f"attachment; filename=nexusai_news_summary_{current_date}.txt"
        response.headers["Content-Type"] = "text/plain"
        
        return response
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        return jsonify({"error": "An error occurred while generating the summary"}), 500

@app.route('/api/articles')
def api_articles():
    """API endpoint to get all articles"""
    # Get limit parameter with default value
    limit = request.args.get('limit', default=12, type=int)
    force_refresh = request.args.get('refresh', default=False, type=bool)
    
    articles = get_articles(force_refresh)
    
    # Filter out hero article (which is returned by the /api/hero endpoint)
    non_hero_articles = [a for a in articles if not a.get('isHero', False)][:limit]
    
    return jsonify({
        'articles': non_hero_articles,
        'lastUpdated': datetime.fromtimestamp(LAST_UPDATED).isoformat() if LAST_UPDATED else None,
        'total': len(articles)
    })

@app.route('/api/hero')
def api_hero():
    """API endpoint to get only the hero article"""
    force_refresh = request.args.get('refresh', default=False, type=bool)
    
    articles = get_articles(force_refresh)
    
    # Find the hero article
    hero = next((article for article in articles if article.get('isHero', False)), None)
    
    # If no hero is designated, use the first article
    if not hero and articles:
        hero = articles[0]
    
    return jsonify({
        'article': hero,
        'lastUpdated': datetime.fromtimestamp(LAST_UPDATED).isoformat() if LAST_UPDATED else None
    })

@app.route('/debug')
def debug_info():
    """Debug endpoint to check app status"""
    return jsonify({
        'status': 'running',
        'articles_count': len(CACHED_ARTICLES),
        'cache_updated': datetime.fromtimestamp(LAST_UPDATED).isoformat() if LAST_UPDATED else None,
        'feeds': RSS_FEEDS,
        'directories': {
            'base_dir': BASE_DIR,
            'files': os.listdir(BASE_DIR)
        }
    })

# When the app starts, try to load cached articles
load_cached_articles()

if __name__ == '__main__':
    # If run directly, start the server
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
