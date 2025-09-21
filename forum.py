import os
import requests
import time
from urllib.parse import quote
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import random
from fake_useragent import UserAgent
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

reddit_access_token = None

def get_reddit_access_token():
    """Get Reddit OAuth access token"""
    global reddit_access_token
    REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
    REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
    REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'LinkSearchBot/1.0')

    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        return None

    try:
        auth = requests.auth.HTTPBasicAuth(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
        data = {'grant_type': 'client_credentials'}
        headers = {'User-Agent': REDDIT_USER_AGENT}

        response = requests.post('https://www.reddit.com/api/v1/access_token',
                               auth=auth, data=data, headers=headers, timeout=10)

        if response.status_code == 200:
            reddit_access_token = response.json()['access_token']
            return reddit_access_token
        else:
            print(f"Failed to get Reddit access token: {response.status_code}")
            return None

    except Exception as e:
        print(f"Reddit authentication error: {e}")
        return None

def search_reddit_api(query, limit=5):
    """Search Reddit using official API"""
    try:
        global reddit_access_token
        if not reddit_access_token:
            token = get_reddit_access_token()
            if not token:
                return []

        headers = {
            'Authorization': f'bearer {reddit_access_token}',
            'User-Agent': os.getenv('REDDIT_USER_AGENT', 'LinkSearchBot/1.0')
        }

        params = {
            'q': query,
            'type': 'link',
            'sort': 'relevance',
            'limit': limit,
            't': 'all'
        }

        response = requests.get('https://oauth.reddit.com/search',
                              headers=headers, params=params, timeout=15)

        if response.status_code == 200:
            data = response.json()
            results = []

            if 'data' in data and 'children' in data['data']:
                for post in data['data']['children']:
                    post_data = post['data']

                    # Skip if no URL or if it's a self post
                    if not post_data.get('url') or post_data.get('is_self'):
                        continue

                    results.append({
                        'title': post_data.get('title', ''),
                        'url': post_data.get('url', ''),
                        'description': f"Discussion in r/{post_data.get('subreddit', '')} - {post_data.get('num_comments', 0)} comments",
                        'subreddit': post_data.get('subreddit', ''),
                        'score': post_data.get('score', 0),
                        'comments': post_data.get('num_comments', 0),
                        'created': post_data.get('created_utc', 0),
                        'source': 'Reddit'
                    })

            return results
        else:
            print(f"Reddit API error: {response.status_code}")
            return []

    except Exception as e:
        print(f"Reddit search error: {e}")
        return []

def search_medium(query, limit=5):
    """Search Medium for blog posts via web scraping with rate limiting and user-agent rotation"""
    try:
        ua = UserAgent()
        headers = {
            'User-Agent': ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
        }
        url = f"https://medium.com/search?q={quote(query)}"
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=15)
        if response.status_code == 429:
            print("Medium rate limit hit. Waiting for 30 seconds...")
            time.sleep(30)
            response = session.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Medium scraping error: Status code {response.status_code}")
            return []
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        articles = soup.find_all('article')[:limit]
        for article in articles:
            title_tag = article.find('h2')
            if not title_tag:
                continue
            title = title_tag.text.strip()
            link_tags = article.find_all('a')
            link = ''
            for a in link_tags:
                href = a.get('href', '')
                if href and (href.startswith('/@') or href.startswith('https://medium.com/')):
                    if not href.startswith('https'):
                        href = 'https://medium.com' + href
                    link = href
                    break
            if not link:
                continue
            desc_tag = article.find('p')
            description = desc_tag.text.strip() if desc_tag else 'No description available'
            results.append({
                'title': title,
                'url': link,
                'description': description,
                'source': 'Medium'
            })
            time.sleep(random.uniform(1, 3))  # Random delay to avoid rate limiting
        return results
    except Exception as e:
        print(f"Medium scraping error: {e}")
        return []

def search_quora(query, limit=5):
    """Search Quora for Q&A discussions using Selenium"""
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        driver = webdriver.Chrome(options=options)
        url = f"https://www.quora.com/search?q={quote(query)}"
        driver.get(url)
        time.sleep(3)  # Allow page to load
        results = []
        questions = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a.question_link'))
        )[:limit]
        for question in questions:
            title_span = question.find_element(By.CSS_SELECTOR, 'span.ui_qtext_rendered_qtext')
            title = title_span.text.strip() if title_span else question.text.strip()
            href = question.get_attribute('href')
            if not href:
                continue
            results.append({
                'title': title,
                'url': href,
                'description': 'Q&A discussion on Quora',
                'source': 'Quora'
            })
        driver.quit()
        return results
    except Exception as e:
        print(f"Quora scraping error: {e}")
        return []