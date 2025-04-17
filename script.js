document.addEventListener('DOMContentLoaded', () => {
    // Initialize theme
    initTheme();
    
    // Fetch and render articles from API
    fetchArticlesFromAPI();
    
    // Setup cleanup (extra protection)
    setupArtifactCleanup();
    
    // Initialize download summary button
    initDownloadSummary();
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

// SOLUTION 2: Complete rewrite of rendering functions using DOM manipulation

// Render the hero article with DOM manipulation to prevent unwanted elements
function renderHeroArticle(article) {
    const heroArticleElement = document.getElementById('hero-article');
    
    // Clear previous content
    heroArticleElement.innerHTML = '';
    
    // Create image
    const img = document.createElement('img');
    img.src = article.image;
    img.alt = article.title;
    heroArticleElement.appendChild(img);
    
    // Create content container
    const content = document.createElement('div');
    content.className = 'hero-article-content';
    
    // Create source info with only name, no logo
    const sourceInfo = document.createElement('div');
    sourceInfo.className = 'source-info';
    
    const sourceName = document.createElement('span');
    sourceName.className = 'source-name';
    sourceName.textContent = article.source.name;
    sourceInfo.appendChild(sourceName);
    
    // Create title
    const title = document.createElement('h2');
    title.textContent = article.title;
    
    // Create link
    const link = document.createElement('a');
    link.className = 'read-more';
    link.href = article.link;
    link.target = '_blank';
    link.textContent = 'Read Full Article';
    
    // Append all elements
    content.appendChild(sourceInfo);
    content.appendChild(title);
    content.appendChild(link);
    heroArticleElement.appendChild(content);
}

// Render the featured articles with DOM manipulation to prevent unwanted elements
function renderFeaturedArticles(articles) {
    const featuredArticlesElement = document.getElementById('featured-articles');
    
    // Clear the container first
    featuredArticlesElement.innerHTML = '';
    
    // Create each article card with DOM methods instead of innerHTML
    articles.forEach(article => {
        // Create article card
        const card = document.createElement('div');
        card.className = 'article-card';
        
        // Create image
        const img = document.createElement('img');
        img.src = article.image;
        img.alt = article.title;
        card.appendChild(img);
        
        // Create content container
        const content = document.createElement('div');
        content.className = 'article-card-content';
        
        // Create source info with only name, no logo
        const sourceInfo = document.createElement('div');
        sourceInfo.className = 'source-info';
        
        const sourceName = document.createElement('span');
        sourceName.className = 'source-name';
        sourceName.textContent = article.source.name;
        sourceInfo.appendChild(sourceName);
        
        // Create title
        const title = document.createElement('h3');
        title.textContent = article.title;
        
        // Create link
        const link = document.createElement('a');
        link.className = 'read-more';
        link.href = article.link;
        link.target = '_blank';
        link.textContent = 'Read Full Article';
        
        // Append all elements
        content.appendChild(sourceInfo);
        content.appendChild(title);
        content.appendChild(link);
        card.appendChild(content);
        
        // Add to container
        featuredArticlesElement.appendChild(card);
    });
}

// Direct render functions just call the main render functions
function renderHeroArticleDirect(article) {
    renderHeroArticle(article);
}

function renderArticlesDirect(articles) {
    renderFeaturedArticles(articles);
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
        console.log('Manual refresh triggered');
    }
});

// Initialize the download summary functionality
function initDownloadSummary() {
    const downloadBtn = document.getElementById('download-summary-btn');
    
    if (downloadBtn) {
        // Make the button a direct link instead of using JavaScript
        downloadBtn.addEventListener('click', (event) => {
            // Show loading state
            const originalText = downloadBtn.innerHTML;
            downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
            downloadBtn.disabled = true;
            
            // Simple approach: Just open the URL directly
            window.open('/test', '_blank');
            
            // Reset button after a short delay
            setTimeout(() => {
                downloadBtn.innerHTML = originalText;
                downloadBtn.disabled = false;
            }, 1500);
        });
        
        // Also add a simple console message to confirm the function is running
        console.log('Download button initialized!');
    } else {
        console.error('Download button not found in the DOM!');
    }
}

// Extra protection: setup artifact cleanup as well
function setupArtifactCleanup() {
    // Function to remove all TechCrunch text nodes and images
    function removeTechCrunchArtifacts() {
        console.log("Running TechCrunch artifact cleanup...");
        
        try {
            // Find all TechCrunch images and remove them
            document.querySelectorAll('img[alt="TechCrunch"]').forEach(img => {
                img.remove();
            });
            
            // Remove any element that just contains TechCrunch
            const walker = document.createTreeWalker(
                document.body, 
                NodeFilter.SHOW_ELEMENT, 
                null, 
                false
            );
            
            let element;
            let elementsToRemove = [];
            
            while (element = walker.nextNode()) {
                if (element.childNodes.length === 1 && 
                    element.childNodes[0].nodeType === Node.TEXT_NODE && 
                    element.childNodes[0].textContent === 'TechCrunch' &&
                    !element.classList.contains('source-name')) {
                    elementsToRemove.push(element);
                }
            }
            
            // Remove identified elements
            elementsToRemove.forEach(el => el.remove());
            
            // Additional aggressive cleanup - find any text node containing just TechCrunch
            const textWalker = document.createTreeWalker(
                document.body, 
                NodeFilter.SHOW_TEXT, 
                null, 
                false
            );
            
            let textNode;
            let textNodesToModify = [];
            
            while (textNode = textWalker.nextNode()) {
                if (textNode.textContent.trim() === 'TechCrunch' &&
                    textNode.parentElement &&
                    !textNode.parentElement.classList.contains('source-name')) {
                    textNodesToModify.push(textNode);
                }
            }
            
            // Remove or modify text nodes
            textNodesToModify.forEach(node => {
                node.textContent = '';
            });
        } catch (error) {
            console.error("Error in cleanup script:", error);
        }
    }
    
    // Run the cleanup on page load
    removeTechCrunchArtifacts();
    
    // Run cleanup multiple times to catch any late-loading artifacts
    setTimeout(removeTechCrunchArtifacts, 500);
    setTimeout(removeTechCrunchArtifacts, 1000);
    setTimeout(removeTechCrunchArtifacts, 2000);
    
    // Set up an observer to monitor DOM changes and remove artifacts
    const observer = new MutationObserver(() => {
        removeTechCrunchArtifacts();
    });
    
    // Start observing the document body
    observer.observe(document.body, { 
        childList: true, 
        subtree: true,
        characterData: true
    });
}
