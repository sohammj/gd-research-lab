import os
import requests
from urllib.parse import quote

def search_github_api(query, limit=5):
    """Search GitHub using official API"""
    try:
        headers = {'User-Agent': 'LinkSearchBot/1.0'}
        if os.getenv('GITHUB_TOKEN'):
            headers['Authorization'] = f'token {os.getenv("GITHUB_TOKEN")}'

        params = {
            'q': query,
            'sort': 'stars',
            'order': 'desc',
            'per_page': limit
        }

        response = requests.get('https://api.github.com/search/repositories',
                              headers=headers, params=params, timeout=15)

        if response.status_code == 200:
            data = response.json()
            results = []

            if 'items' in data:
                for repo in data['items']:
                    results.append({
                        'title': repo['full_name'],
                        'url': repo['html_url'],
                        'description': repo.get('description', 'No description available'),
                        'stars': repo.get('stargazers_count', 0),
                        'forks': repo.get('forks_count', 0),
                        'language': repo.get('language', 'Unknown'),
                        'updated': repo.get('updated_at', ''),
                        'topics': repo.get('topics', []),
                        'source': 'GitHub'
                    })

            return results
        else:
            print(f"GitHub API error: {response.status_code}")
            return []

    except Exception as e:
        print(f"GitHub search error: {e}")
        return []

def search_kaggle(query, limit=5):
    """Search Kaggle for datasets"""
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        if not os.getenv('KAGGLE_USERNAME') or not os.getenv('KAGGLE_KEY'):
            print("Kaggle search error: KAGGLE_USERNAME and KAGGLE_KEY must be set in .env file")
            return []
        os.environ['KAGGLE_USERNAME'] = os.getenv('KAGGLE_USERNAME')
        os.environ['KAGGLE_KEY'] = os.getenv('KAGGLE_KEY')
        api = KaggleApi()
        api.authenticate()
        datasets = api.dataset_list(search=query, sort_by='votes', max_size=limit)
        results = []
        for ds in datasets:
            votes = getattr(ds, 'upvoteCount', 0)
            results.append({
                'title': ds.title,
                'url': f"https://www.kaggle.com/datasets/{ds.ref}",
                'description': ds.subtitle or 'No description available',
                'votes': votes,
                'source': 'Kaggle'
            })
        return results
    except ImportError as e:
        print(f"Kaggle search error: Failed to import KaggleApi. Ensure 'kaggle' package is installed (pip install kaggle --upgrade). Error: {e}")
        return []
    except Exception as e:
        print(f"Kaggle search error: {e}. Ensure Kaggle API credentials are valid and try again.")
        return []
