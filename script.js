document.addEventListener('DOMContentLoaded', () => {
    // Initialize theme
    initTheme();
    
    // Fetch and render articles from API
    fetchArticlesFromAPI();
});

// Theme toggle functionality
function initTheme() {
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const htmlElement = document.documentElement;
    
    // Check for saved theme preference or use preferred color scheme
    const savedTheme = localStorage.getItem('theme');
    
    if (savedTheme) {
        htmlElement.setAttribute('data-theme', savedTheme);
    } else {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        htmlElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
    }
    
    // Theme toggle button click event
    themeToggleBtn.addEventListener('click', () => {
        const currentTheme = htmlElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        htmlElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    });
}

// Configuration for API endpoints
const API_CONFIG = {
    // Determine base URL dynamically
    BASE_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
        ? 'http://localhost:5001' 
        : '', // Empty string means same domain for production
    ARTICLES_ENDPOINT: '/api/articles',
    HERO_ENDPOINT: '/api/hero',
    LIMIT: 12 // Number of articles to fetch
};

// Fallback articles in case the API is not available
const FALLBACK_ARTICLES = [
    {
        id: 1,
        title: "OpenAI Unveils GPT-5 with Unprecedented Multimodal Capabilities",
        summary: "The latest model from OpenAI shows remarkable improvements in reasoning, visual understanding, and code generation, setting new benchmarks across all major AI evaluation metrics.",
        image: "https://images.unsplash.com/photo-1677442135046-c10d516d84c6?q=80&w=1932&auto=format&fit=crop",
        source: {
            name: 'TechCrunch',
            url: 'https://techcrunch.com',
            logo: 'https://techcrunch.com/wp-content/uploads/2015/02/cropped-cropped-favicon-gradient.png'
        },
        link: "https://techcrunch.com/ai/openai-gpt5-announcement",
        isHero: true
    },
    {
        id: 2,
        title: "EU Passes Comprehensive AI Regulation Framework",
        summary: "The European Union has finalized its AI Act, establishing the world's most stringent rules for artificial intelligence development and deployment.",
        image: "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?q=80&w=1770&auto=format&fit=crop",
        source: {
            name: 'MIT Technology Review',
            url: 'https://www.technologyreview.com',
            logo: 'https://www.technologyreview.com/favicon.ico'
        },
        link: "https://www.technologyreview.com/europe-ai-act-regulation"
    },
    {
        id: 3,
        title: "Google DeepMind's AlphaFold 3 Makes Breakthrough in Protein Structure Prediction",
        summary: "The latest iteration of AlphaFold can now predict protein interactions and small molecule binding with unprecedented accuracy.",
        image: "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?q=80&w=1770&auto=format&fit=crop",
        source: {
            name: 'Wired',
            url: 'https://www.wired.com',
            logo: 'https://www.wired.com/favicon.ico'
        },
        link: "https://www.wired.com/google-deepmind-alphafold3"
    }
];

// Fetch articles from our API endpoints
async function fetchArticlesFromAPI() {
    try {
        console.log('Starting to fetch articles from API...');
        
        // Show loading state
        document.getElementById('hero-article').innerHTML = '<div class="loading">Loading headline article...</div>';
        document.getElementById('featured-articles').innerHTML = '<div class="loading">Loading articles...</div>';
        
        // Fetch hero article with explicit CORS settings
        console.log(`Fetching hero article from: ${API_CONFIG.BASE_URL}${API_CONFIG.HERO_ENDPOINT}`);
        const heroResponse = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.HERO_ENDPOINT}`, {
            method: 'GET',
            mode: 'cors',
            credentials: 'same-origin',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        if (!heroResponse.ok) {
            console.error(`Hero article fetch failed with status: ${heroResponse.status}`);
            throw new Error(`Failed to fetch hero article: ${heroResponse.statusText}`);
        }
        
        const heroData = await heroResponse.json();
        console.log('Hero article data received:', heroData);
        
        // Fetch featured articles with explicit CORS settings
        console.log(`Fetching articles from: ${API_CONFIG.BASE_URL}${API_CONFIG.ARTICLES_ENDPOINT}?limit=${API_CONFIG.LIMIT}`);
        const articlesResponse = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ARTICLES_ENDPOINT}?limit=${API_CONFIG.LIMIT}`, {
            method: 'GET',
            mode: 'cors',
            credentials: 'same-origin',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        if (!articlesResponse.ok) {
            console.error(`Articles fetch failed with status: ${articlesResponse.status}`);
            throw new Error(`Failed to fetch articles: ${articlesResponse.statusText}`);
        }
        
        const articlesData = await articlesResponse.json();
        console.log('Articles data received:', articlesData);
        
        // Get the hero article
        const heroArticle = heroData.article;
        
        // Filter out the hero article from the featured articles
        const featuredArticles = articlesData.articles.filter(article => 
            !article.isHero && article.id !== (heroArticle ? heroArticle.id : null)
        );
        
        // Render articles
        if (heroArticle) {
            renderHeroArticle(heroArticle);
        } else {
            // Fallback to first article if no hero is designated
            renderHeroArticle(featuredArticles[0] || FALLBACK_ARTICLES[0]);
            // Remove the first article from featured if we used it as hero
            if (featuredArticles.length > 0) featuredArticles.shift();
        }
        
        renderFeaturedArticles(featuredArticles.length > 0 ? featuredArticles : FALLBACK_ARTICLES.slice(1));
        
        // Update last fetched time in footer if available
        if (articlesData.lastUpdated) {
            const lastUpdated = new Date(articlesData.lastUpdated);
            const footerInfo = document.querySelector('.footer-bottom p');
            if (footerInfo) {
                footerInfo.innerHTML = `&copy; ${new Date().getFullYear()} NexusAI. Articles last updated: ${lastUpdated.toLocaleString()}`;
            }
        }
        
    } catch (error) {
        console.error('Error fetching articles:', error);
        console.log('Browser details:', navigator.userAgent);
        console.log('Possible CORS issue - check if the API server has CORS enabled');
        
        // Add a visual indicator for debugging
        const debugInfo = document.createElement('div');
        debugInfo.style.position = 'fixed';
        debugInfo.style.top = '0';
        debugInfo.style.left = '0';
        debugInfo.style.backgroundColor = 'rgba(255,0,0,0.7)';
        debugInfo.style.color = 'white';
        debugInfo.style.padding = '10px';
        debugInfo.style.zIndex = '9999';
        debugInfo.style.maxWidth = '80%';
        debugInfo.style.wordBreak = 'break-word';
        debugInfo.innerHTML = `Error: ${error.message}<br>API URL: ${API_CONFIG.BASE_URL}<br>Try opening browser console for more details`;
        document.body.appendChild(debugInfo);
        
        // Fall back to sample data if API fails
        console.log('Falling back to sample data');
        const heroArticle = FALLBACK_ARTICLES.find(article => article.isHero);
        const featuredArticles = FALLBACK_ARTICLES.filter(article => !article.isHero);
        
        renderHeroArticle(heroArticle || FALLBACK_ARTICLES[0]);
        renderFeaturedArticles(featuredArticles);
        
        // Show error message
        const footer = document.querySelector('.footer-bottom p');
        if (footer) {
            footer.innerHTML = `&copy; ${new Date().getFullYear()} NexusAI. Using sample data (API unavailable). ${error.message}`;
        }
    }
}

// Render the hero article
function renderHeroArticle(article) {
    const heroArticleElement = document.getElementById('hero-article');
    
    heroArticleElement.innerHTML = `
        <img src="${article.image}" alt="${article.title}">
        <div class="hero-article-content">
            <div class="source-info">
                <img src="${article.source.logo}" alt="${article.source.name}" class="source-logo">
                <span class="source-name">${article.source.name}</span>
            </div>
            <h2>${article.title}</h2>
            <a href="${article.link}" class="read-more" target="_blank">Read Full Article</a>
        </div>
    `;
}

// Render the featured articles
function renderFeaturedArticles(articles) {
    const featuredArticlesElement = document.getElementById('featured-articles');
    
    featuredArticlesElement.innerHTML = articles.map(article => `
        <div class="article-card">
            <img src="${article.image}" alt="${article.title}">
            <div class="article-card-content">
                <div class="source-info">
                    <img src="${article.source.logo}" alt="${article.source.name}" class="source-logo">
                    <span class="source-name">${article.source.name}</span>
                </div>
                <h3>${article.title}</h3>
                <a href="${article.link}" class="read-more" target="_blank">Read Full Article</a>
            </div>
        </div>
    `).join('');
}

// Add a function to periodically refresh articles
function setupArticleRefresh() {
    // Refresh articles every 15 minutes
    setInterval(() => {
        console.log('Refreshing articles...');
        fetchArticlesFromAPI();
    }, 15 * 60 * 1000); // 15 minutes in milliseconds
}

// Call this after initial fetch
setupArticleRefresh();

// Add event listener for manual refresh
document.addEventListener('keydown', (event) => {
    // Refresh on F5 or Ctrl+R without reloading the page
    if (event.key === 'F5' || (event.ctrlKey && event.key === 'r')) {
        event.preventDefault();
        fetchArticlesFromAPI();
    }
});
