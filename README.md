# NexusAI - AI News Hub

A modern, responsive website that showcases the latest AI news from various open sources, dynamically fetched from RSS feeds.

## Features

- **Modern Design**: Clean and contemporary UI with responsive layout
- **Dark/Light Mode**: Toggle between light and dark themes based on preference
- **RSS Integration**: Live articles fetched from RSS feeds of major tech publications
- **Custom API**: Backend API that aggregates and filters AI-specific content
- **Multiple Sources**: News from 6 different technology news sources
- **Featured Hero Article**: Main headline article in hero position
- **Responsive Layout**: Optimized for all device sizes
- **Auto-Refresh**: Articles automatically refresh every 15 minutes

## How to Use

1. Clone this repository or download the files
2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```
3. Start the API server:
   ```
   python api.py
   ```
4. Open your browser and navigate to `http://localhost:5001`
5. Toggle between dark and light mode using the button in the header
6. Articles will automatically refresh every 15 minutes

## Implementation Details

### RSS Feed Integration

The application pulls news from the RSS feeds of major technology publications and filters them for AI-related content. The backend uses the following components:

- **feedparser**: Python library to parse RSS feeds from news sources
- **Flask**: Web framework for creating the API endpoints
- **BeautifulSoup**: For extracting article summaries and images from HTML content
- **Thread-based Background Fetching**: Periodically updates the article cache

### API Endpoints

- `/api/articles` - Returns a list of all articles
- `/api/hero` - Returns the designated hero article for the main feature

### Files

- `index.html` - Main HTML structure of the website
- `styles.css` - All styling including dark/light mode themes
- `script.js` - JavaScript for theme toggling, API calls, and article rendering
- `api.py` - Python backend that fetches and serves RSS content
- `requirements.txt` - Required Python dependencies
- `server.py` - Simple HTTP server (alternative to Flask for static serving only)

### Future Enhancements

To further enhance this news aggregator, consider:

1. Implementing more sophisticated content filtering and AI topic classification
2. Adding user authentication for personalized news preferences and saved articles
3. Implementing a search feature to find specific AI topics
4. Adding categorization of AI news by subcategories (e.g., Machine Learning, NLP, Computer Vision)
5. Creating a database backend for more efficient article storage and retrieval
6. Adding a sentiment analysis feature to categorize articles by tone
7. Implementing social media sharing capabilities
8. Creating an email newsletter feature using the collected articles

## Credits

- Font Awesome icons
- Google Fonts (Inter)
- Unsplash for fallback images
- RSS feeds from TechCrunch, MIT Technology Review, Wired, VentureBeat, The Verge, and Ars Technica
- Python libraries: Flask, feedparser, BeautifulSoup4, and requests

## License

This project is for demonstration purposes.

## Troubleshooting

If you encounter issues:

1. Make sure all Python dependencies are installed
2. Check if the RSS feeds are accessible
3. The application includes fallback content if feeds are unavailable
4. Look for error messages in the browser console or terminal output
