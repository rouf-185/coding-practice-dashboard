import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def scrape_leetcode_problem(url):
    """
    Scrape Leetcode problem page to extract title and difficulty.
    
    Args:
        url: Leetcode problem URL (e.g., https://leetcode.com/problems/four-divisors/description/)
    
    Returns:
        dict with 'title' and 'difficulty' keys, or None if scraping fails
    """
    try:
        # Add headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title - Leetcode typically has it in the page title or in a specific div
        title = None
        
        # Try to get from page title
        page_title = soup.find('title')
        if page_title:
            title_text = page_title.get_text()
            # Leetcode titles are usually in format "Problem Name - LeetCode"
            if ' - LeetCode' in title_text:
                title = title_text.replace(' - LeetCode', '').strip()
            else:
                title = title_text.strip()
        
        # If not found in title, try to find in the page content
        if not title:
            # Look for common Leetcode title patterns
            title_elem = soup.find('div', class_=re.compile(r'.*title.*', re.I))
            if title_elem:
                title = title_elem.get_text().strip()
        
        # Extract difficulty
        difficulty = None
        difficulty_map = {'easy': 'easy', 'medium': 'medium', 'hard': 'hard'}
        
        # Look for difficulty indicators in the page
        difficulty_elem = soup.find(string=re.compile(r'(Easy|Medium|Hard)', re.I))
        if difficulty_elem:
            difficulty_text = difficulty_elem.strip().lower()
            for key in difficulty_map:
                if key in difficulty_text:
                    difficulty = difficulty_map[key]
                    break
        
        # Also check in class names or data attributes
        if not difficulty:
            difficulty_elem = soup.find(class_=re.compile(r'.*difficulty.*', re.I))
            if difficulty_elem:
                difficulty_text = difficulty_elem.get_text().strip().lower()
                for key in difficulty_map:
                    if key in difficulty_text:
                        difficulty = difficulty_map[key]
                        break
        
        # Fallback: try to extract from URL or use a default
        if not difficulty:
            # Some Leetcode URLs might have difficulty in them, but usually not
            # Default to medium if we can't determine
            difficulty = 'medium'
        
        # If we still don't have a title, try to extract from URL
        if not title:
            # Extract problem slug from URL
            parsed = urlparse(url)
            path_parts = parsed.path.strip('/').split('/')
            if 'problems' in path_parts:
                idx = path_parts.index('problems')
                if idx + 1 < len(path_parts):
                    slug = path_parts[idx + 1]
                    # Convert slug to title (e.g., "four-divisors" -> "Four Divisors")
                    title = ' '.join(word.capitalize() for word in slug.split('-'))
        
        if not title:
            return None
        
        return {
            'title': title,
            'difficulty': difficulty
        }
    
    except Exception as e:
        print(f"Error scraping Leetcode: {str(e)}")
        return None

