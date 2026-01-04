import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time


def scrape_leetcode_problem(url):
    """
    Scrape Leetcode problem page to extract title and difficulty.
    Uses Selenium for JavaScript-rendered content.
    
    Args:
        url: Leetcode problem URL (e.g., https://leetcode.com/problems/four-divisors/description/)
    
    Returns:
        dict with 'title' and 'difficulty' keys, or None if scraping fails
    """
    try:
        # First try with requests (faster if it works)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check if page is JavaScript-rendered (Cloudflare protection)
        page_text = soup.get_text()
        if 'Just a moment' in page_text or 'Checking your browser' in page_text or len(page_text) < 100:
            # Use Selenium for JavaScript rendering
            return scrape_with_selenium(url)
        
        # Extract title - multiple strategies
        title = None
        
        # Strategy 1: Get from page title tag
        page_title = soup.find('title')
        if page_title:
            title_text = page_title.get_text()
            # Leetcode titles are usually in format "Problem Name - LeetCode"
            if ' - LeetCode' in title_text:
                title = title_text.replace(' - LeetCode', '').strip()
            elif ' | LeetCode' in title_text:
                title = title_text.replace(' | LeetCode', '').strip()
            else:
                title = title_text.strip()
        
        # Strategy 2: Look for data attributes or specific divs
        if not title or len(title) < 3:
            # Try to find in meta tags
            meta_title = soup.find('meta', property='og:title')
            if meta_title and meta_title.get('content'):
                title = meta_title.get('content').replace(' - LeetCode', '').replace(' | LeetCode', '').strip()
        
        # Strategy 3: Look for h1 or specific class patterns
        if not title or len(title) < 3:
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text().strip()
        
        # Strategy 4: Extract from URL slug as fallback
        if not title or len(title) < 3:
            parsed = urlparse(url)
            path_parts = parsed.path.strip('/').split('/')
            if 'problems' in path_parts:
                idx = path_parts.index('problems')
                if idx + 1 < len(path_parts):
                    slug = path_parts[idx + 1]
                    # Convert slug to title (e.g., "n-repeated-element-in-size-2n-array" -> "N Repeated Element In Size 2n Array")
                    title = ' '.join(word.capitalize() for word in slug.split('-'))
        
        # Extract difficulty - multiple strategies (prioritize more specific patterns)
        difficulty = None
        difficulty_map = {'easy': 'easy', 'medium': 'medium', 'hard': 'hard'}
        
        # Strategy 1: Look for difficulty in specific data attributes (most reliable)
        # Leetcode often stores difficulty in data attributes
        difficulty_elem = soup.find(attrs={'data-difficulty': True})
        if difficulty_elem:
            diff_attr = difficulty_elem.get('data-difficulty', '').lower()
            if diff_attr in difficulty_map:
                difficulty = difficulty_map[diff_attr]
        
        # Strategy 2: Look for Leetcode's specific difficulty badge classes
        # Leetcode uses classes like "text-difficulty-hard", "text-difficulty-medium", "text-difficulty-easy"
        # Pattern: class="... text-difficulty-hard ..." or "dark:text-difficulty-hard"
        # Find all elements with text-difficulty-* classes and match both class and text
        if not difficulty:
            # Find all elements with any text-difficulty-* class
            all_difficulty_elems = soup.find_all(class_=re.compile(r'text-difficulty-(hard|medium|easy)', re.I))
            
            # Check each element to find the one with matching text
            for elem in all_difficulty_elems:
                text = elem.get_text().strip()
                classes = ' '.join(elem.get('class', []))
                
                # Check which difficulty level matches both class and text exactly
                if text == 'Easy' and 'text-difficulty-easy' in classes.lower():
                    difficulty = 'easy'
                    break
                elif text == 'Medium' and 'text-difficulty-medium' in classes.lower():
                    difficulty = 'medium'
                    break
                elif text == 'Hard' and 'text-difficulty-hard' in classes.lower():
                    difficulty = 'hard'
                    break
        
        # Strategy 2b: Look for other difficulty badge class patterns
        if not difficulty:
            for key in ['hard', 'medium', 'easy']:  # Check hard first since it's most specific
                # Look for class patterns like "difficulty-hard", "hard-difficulty", etc.
                patterns = [
                    f'difficulty-{key}',
                    f'{key}-difficulty',
                    f'difficulty.*{key}',
                    f'{key}.*difficulty'
                ]
                for pattern in patterns:
                    elem = soup.find(class_=re.compile(pattern, re.I))
                    if elem:
                        # Verify it's actually a difficulty indicator
                        text = elem.get_text().strip().lower()
                        if key in text or len(text) < 20:
                            difficulty = difficulty_map[key]
                            break
                if difficulty:
                    break
        
        # Strategy 3: Look for difficulty in class names with specific patterns
        if not difficulty:
            # Look for elements with difficulty in class name
            for elem in soup.find_all(class_=re.compile(r'difficulty', re.I)):
                classes = ' '.join(elem.get('class', []))
                text = elem.get_text().strip().lower()
                # Check if class name contains difficulty level
                for key in ['hard', 'medium', 'easy']:  # Check hard first
                    if f'difficulty-{key}' in classes.lower() or f'{key}-difficulty' in classes.lower():
                        difficulty = difficulty_map[key]
                        break
                    # Also check text content if it's short (likely a badge)
                    if key in text and len(text) < 20:
                        # Make sure it's not part of a longer word
                        if re.search(rf'\b{key}\b', text):
                            difficulty = difficulty_map[key]
                            break
                if difficulty:
                    break
        
        # Strategy 4: Look for difficulty badges/buttons near the title (common Leetcode pattern)
        if not difficulty:
            # Find title area and look for difficulty nearby
            title_area = soup.find(['h1', 'h2', 'div'], class_=re.compile(r'title|problem', re.I))
            if title_area:
                # Look in parent, siblings, and nearby elements
                search_areas = []
                if title_area.parent:
                    search_areas.append(title_area.parent)
                # Look for next sibling
                if title_area.next_sibling:
                    search_areas.append(title_area.next_sibling)
                # Look in the same container
                container = title_area.find_parent(['div', 'section'])
                if container:
                    search_areas.append(container)
                
                for area in search_areas:
                    if area:
                        # Look for exact matches first
                        for key in ['hard', 'medium', 'easy']:
                            # Look for elements with the difficulty text
                            elems = area.find_all(['span', 'div', 'button', 'a'], 
                                                 string=re.compile(rf'^{key.capitalize()}$', re.I))
                            if elems:
                                # Check if it's in a difficulty-related context
                                for elem in elems:
                                    parent_classes = ' '.join(elem.parent.get('class', []) if elem.parent else [])
                                    elem_classes = ' '.join(elem.get('class', []))
                                    all_classes = (parent_classes + ' ' + elem_classes).lower()
                                    # If it has difficulty-related classes or is near the title, it's likely correct
                                    if 'difficulty' in all_classes or 'badge' in all_classes or 'tag' in all_classes:
                                        difficulty = difficulty_map[key]
                                        break
                                if difficulty:
                                    break
                        if difficulty:
                            break
        
        # Strategy 5: Look for difficulty in JSON-LD structured data
        if not difficulty:
            json_ld = soup.find('script', type='application/ld+json')
            if json_ld:
                try:
                    import json
                    data = json.loads(json_ld.string)
                    if isinstance(data, dict):
                        # Check various possible keys
                        for key in ['difficulty', 'level', 'complexity']:
                            if key in data:
                                diff_val = str(data[key]).lower()
                                if diff_val in difficulty_map:
                                    difficulty = difficulty_map[diff_val]
                                    break
                except:
                    pass
        
        # Strategy 6: Look for difficulty in page text with more specific patterns
        if not difficulty:
            page_text = soup.get_text()
            # Look for patterns that are more specific to difficulty indicators
            patterns = [
                r'Difficulty\s*:?\s*(Easy|Medium|Hard)',
                r'Level\s*:?\s*(Easy|Medium|Hard)',
                r'"(Easy|Medium|Hard)"\s*:?\s*true',  # JSON-like patterns
                r'\b(Hard|Medium|Easy)\b.*difficulty',  # "Hard difficulty" pattern
                r'difficulty.*\b(Hard|Medium|Easy)\b',  # "difficulty: Hard" pattern
            ]
            for pattern in patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    diff_text = match.group(1).lower()
                    if diff_text in difficulty_map:
                        difficulty = difficulty_map[diff_text]
                        break
        
        # Strategy 7: Look for exact text matches in buttons/spans (last resort)
        if not difficulty:
            for key in ['hard', 'medium', 'easy']:  # Check hard first
                elements = soup.find_all(['button', 'span', 'div', 'p', 'a'], 
                                       string=re.compile(rf'^{key.capitalize()}$', re.I))
                if elements:
                    # Prefer elements that are likely to be difficulty indicators
                    for elem in elements:
                        # Check if it's in a likely difficulty context
                        parent_classes = ' '.join(elem.parent.get('class', []) if elem.parent else [])
                        elem_classes = ' '.join(elem.get('class', []))
                        all_classes = (parent_classes + ' ' + elem_classes).lower()
                        if 'difficulty' in all_classes or 'badge' in all_classes or 'tag' in all_classes:
                            diff_text = elem.get_text().strip().lower()
                            if diff_text in difficulty_map:
                                difficulty = difficulty_map[diff_text]
                                break
                    if difficulty:
                        break
        
        # Fallback: default to medium if we can't determine
        if not difficulty:
            difficulty = 'medium'
        
        # Final validation
        if not title or len(title) < 3:
            return None
        
        return {
            'title': title,
            'difficulty': difficulty
        }
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Leetcode page: {str(e)}")
        return None
    except Exception as e:
        print(f"Error scraping Leetcode: {str(e)}")
        # Try Selenium as fallback
        try:
            return scrape_with_selenium(url)
        except Exception as selenium_error:
            print(f"Error with Selenium: {str(selenium_error)}")
            # Try URL-based fallback
            try:
                parsed = urlparse(url)
                path_parts = parsed.path.strip('/').split('/')
                if 'problems' in path_parts:
                    idx = path_parts.index('problems')
                    if idx + 1 < len(path_parts):
                        slug = path_parts[idx + 1]
                        title = ' '.join(word.capitalize() for word in slug.split('-'))
                        return {
                            'title': title,
                            'difficulty': 'medium'  # Default
                        }
            except:
                pass
            return None


def scrape_with_selenium(url):
    """
    Scrape Leetcode using Selenium to handle JavaScript-rendered content.
    
    Args:
        url: Leetcode problem URL
    
    Returns:
        dict with 'title' and 'difficulty' keys, or None if scraping fails
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager
        
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Initialize driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        try:
            driver.get(url)
            # Wait for page to load (wait for title element or difficulty badge)
            wait = WebDriverWait(driver, 15)
            
            # Wait for either title or difficulty to appear
            try:
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            except:
                # If h1 doesn't appear, wait a bit more for JavaScript to render
                time.sleep(3)
            
            # Get page source after JavaScript rendering
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract title
            title = None
            page_title = soup.find('title')
            if page_title:
                title_text = page_title.get_text()
                if ' - LeetCode' in title_text:
                    title = title_text.replace(' - LeetCode', '').strip()
                elif ' | LeetCode' in title_text:
                    title = title_text.replace(' | LeetCode', '').strip()
                else:
                    title = title_text.strip()
            
            # Try to find h1
            if not title or len(title) < 3:
                h1 = soup.find('h1')
                if h1:
                    title = h1.get_text().strip()
            
            # Extract difficulty - try multiple strategies
            difficulty = None
            difficulty_map = {'easy': 'easy', 'medium': 'medium', 'hard': 'hard'}
            
            # Strategy 1: Look for text-difficulty-* classes
            if not difficulty:
                for key in ['hard', 'medium', 'easy']:
                    elems = soup.find_all(class_=re.compile(rf'text-difficulty-{key}', re.I))
                    for elem in elems:
                        text = elem.get_text().strip()
                        if text in ['Easy', 'Medium', 'Hard']:
                            if (key == 'easy' and text == 'Easy') or \
                               (key == 'medium' and text == 'Medium') or \
                               (key == 'hard' and text == 'Hard'):
                                difficulty = difficulty_map[key]
                                break
                    if difficulty:
                        break
            
            # Strategy 2: Look for data-difficulty attribute
            if not difficulty:
                diff_elem = soup.find(attrs={'data-difficulty': True})
                if diff_elem:
                    diff_attr = diff_elem.get('data-difficulty', '').lower()
                    if diff_attr in difficulty_map:
                        difficulty = difficulty_map[diff_attr]
            
            # Strategy 3: Look for difficulty in text near title
            if not difficulty:
                page_text = soup.get_text()
                for level in ['Hard', 'Medium', 'Easy']:
                    if level in page_text:
                        # Check if it's in a difficulty context
                        idx = page_text.find(level)
                        context = page_text[max(0, idx-30):idx+30].lower()
                        if 'difficulty' in context or 'level' in context:
                            difficulty = difficulty_map[level.lower()]
                            break
            
            # Fallback: default to medium
            if not difficulty:
                difficulty = 'medium'
            
            # Final validation
            if not title or len(title) < 3:
                # Extract from URL
                parsed = urlparse(url)
                path_parts = parsed.path.strip('/').split('/')
                if 'problems' in path_parts:
                    idx = path_parts.index('problems')
                    if idx + 1 < len(path_parts):
                        slug = path_parts[idx + 1]
                        title = ' '.join(word.capitalize() for word in slug.split('-'))
            
            return {
                'title': title,
                'difficulty': difficulty
            }
            
        finally:
            driver.quit()
            
    except ImportError:
        # Selenium not available, fall back to URL-based extraction
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        if 'problems' in path_parts:
            idx = path_parts.index('problems')
            if idx + 1 < len(path_parts):
                slug = path_parts[idx + 1]
                title = ' '.join(word.capitalize() for word in slug.split('-'))
                return {
                    'title': title,
                    'difficulty': 'medium'  # Default
                }
        return None
    except Exception as e:
        print(f"Error in Selenium scraping: {str(e)}")
        return None
