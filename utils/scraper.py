"""
Leetcode problem scraper.
"""
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import Optional, Dict


def scrape_leetcode_problem(url: str) -> Optional[Dict[str, str]]:
    """
    Scrape Leetcode problem page to extract title and difficulty.
    
    Args:
        url: Leetcode problem URL
    
    Returns:
        dict with 'title' and 'difficulty' keys, or None if scraping fails
    """
    try:
        # First try with requests (faster)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check if page is JavaScript-rendered (Cloudflare protection)
        page_text = soup.get_text()
        if 'Just a moment' in page_text or 'Checking your browser' in page_text or len(page_text) < 100:
            return _scrape_with_selenium(url)
        
        title = _extract_title(soup, url)
        difficulty = _extract_difficulty(soup)
        
        if not title or len(title) < 3:
            return None
        
        return {'title': title, 'difficulty': difficulty or 'medium'}
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Leetcode page: {e}")
        return None
    except Exception as e:
        print(f"Error scraping Leetcode: {e}")
        try:
            return _scrape_with_selenium(url)
        except Exception:
            return _extract_from_url(url)


def _extract_title(soup: BeautifulSoup, url: str) -> Optional[str]:
    """Extract problem title from page."""
    title = None
    
    # Strategy 1: Page title tag
    page_title = soup.find('title')
    if page_title:
        title_text = page_title.get_text()
        for suffix in [' - LeetCode', ' | LeetCode']:
            if suffix in title_text:
                title = title_text.replace(suffix, '').strip()
                break
        if not title:
            title = title_text.strip()
    
    # Strategy 2: Meta tags
    if not title or len(title) < 3:
        meta_title = soup.find('meta', property='og:title')
        if meta_title and meta_title.get('content'):
            title = meta_title.get('content').replace(' - LeetCode', '').replace(' | LeetCode', '').strip()
    
    # Strategy 3: H1 tag
    if not title or len(title) < 3:
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text().strip()
    
    # Strategy 4: Extract from URL
    if not title or len(title) < 3:
        result = _extract_from_url(url)
        if result:
            title = result['title']
    
    return title


def _extract_difficulty(soup: BeautifulSoup) -> Optional[str]:
    """Extract problem difficulty from page."""
    difficulty_map = {'easy': 'easy', 'medium': 'medium', 'hard': 'hard'}
    
    # Strategy 1: Data attribute
    diff_elem = soup.find(attrs={'data-difficulty': True})
    if diff_elem:
        diff_attr = diff_elem.get('data-difficulty', '').lower()
        if diff_attr in difficulty_map:
            return difficulty_map[diff_attr]
    
    # Strategy 2: text-difficulty-* classes
    for key in ['hard', 'medium', 'easy']:
        elems = soup.find_all(class_=re.compile(rf'text-difficulty-{key}', re.I))
        for elem in elems:
            text = elem.get_text().strip()
            if text.lower() == key:
                return difficulty_map[key]
    
    # Strategy 3: Class patterns
    for key in ['hard', 'medium', 'easy']:
        patterns = [f'difficulty-{key}', f'{key}-difficulty']
        for pattern in patterns:
            elem = soup.find(class_=re.compile(pattern, re.I))
            if elem:
                return difficulty_map[key]
    
    # Strategy 4: Text patterns
    page_text = soup.get_text()
    patterns = [
        r'Difficulty\s*:?\s*(Easy|Medium|Hard)',
        r'Level\s*:?\s*(Easy|Medium|Hard)',
    ]
    for pattern in patterns:
        match = re.search(pattern, page_text, re.IGNORECASE)
        if match:
            return difficulty_map[match.group(1).lower()]
    
    return None


def _extract_from_url(url: str) -> Optional[Dict[str, str]]:
    """Extract problem info from URL slug."""
    try:
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        if 'problems' in path_parts:
            idx = path_parts.index('problems')
            if idx + 1 < len(path_parts):
                slug = path_parts[idx + 1]
                title = ' '.join(word.capitalize() for word in slug.split('-'))
                return {'title': title, 'difficulty': 'medium'}
    except Exception:
        pass
    return None


def _scrape_with_selenium(url: str) -> Optional[Dict[str, str]]:
    """
    Scrape using Selenium for JavaScript-rendered content.
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        try:
            driver.get(url)
            wait = WebDriverWait(driver, 15)
            
            try:
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            except Exception:
                time.sleep(3)
            
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            title = _extract_title(soup, url)
            difficulty = _extract_difficulty(soup)
            
            if not title or len(title) < 3:
                result = _extract_from_url(url)
                if result:
                    title = result['title']
            
            return {'title': title, 'difficulty': difficulty or 'medium'}
        finally:
            driver.quit()
            
    except ImportError:
        return _extract_from_url(url)
    except Exception as e:
        print(f"Selenium error: {e}")
        return _extract_from_url(url)
