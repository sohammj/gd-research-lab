import os
import requests

def search_semantic_scholar(query, limit=5):
    """Search Semantic Scholar for academic papers"""
    try:
        SEMANTIC_SCHOLAR_API_KEY = os.getenv('SEMANTIC_SCHOLAR_API_KEY')
        if not SEMANTIC_SCHOLAR_API_KEY:
            return []

        headers = {
            'X-API-KEY': SEMANTIC_SCHOLAR_API_KEY
        }

        params = {
            'query': query,
            'limit': limit,
            'fields': 'title,authors,year,url,abstract,citationCount,venue,publicationTypes'
        }

        response = requests.get('https://api.semanticscholar.org/graph/v1/paper/search',
                              headers=headers, params=params, timeout=15)

        if response.status_code == 200:
            data = response.json()
            results = []

            if 'data' in data:
                for paper in data['data']:
                    if not paper.get('url'):
                        continue

                    authors = []
                    if paper.get('authors'):
                        authors = [author.get('name', '') for author in paper['authors'][:3]]
                        if len(paper['authors']) > 3:
                            authors.append('et al.')

                    results.append({
                        'title': paper.get('title', ''),
                        'url': paper.get('url', ''),
                        'description': paper.get('abstract', '')[:200] + '...' if paper.get('abstract') else 'No abstract available',
                        'authors': ', '.join(authors),
                        'year': paper.get('year', 'Unknown'),
                        'citations': paper.get('citationCount', 0),
                        'venue': paper.get('venue', 'Unknown'),
                        'types': paper.get('publicationTypes', []),
                        'source': 'Semantic Scholar'
                    })

            return results
        else:
            print(f"Semantic Scholar API error: {response.status_code}")
            return []

    except Exception as e:
        print(f"Semantic Scholar search error: {e}")
        return []

def search_google_scholar_serpapi(query, limit=5):
    """Search Google Scholar using SerpAPI"""
    try:
        SERPAPI_KEY = os.getenv('SERPAPI_KEY')
        if not SERPAPI_KEY:
            return []

        params = {
            'engine': 'google_scholar',
            'q': query,
            'api_key': SERPAPI_KEY,
            'num': limit,
            'hl': 'en'
        }

        response = requests.get('https://serpapi.com/search', params=params, timeout=15)

        if response.status_code == 200:
            data = response.json()
            results = []

            if 'organic_results' in data:
                for result in data['organic_results']:
                    if not result.get('link'):
                        continue

                    pub_info = result.get('publication_info', {})
                    inline_links = result.get('inline_links', {})
                    cited_by = inline_links.get('cited_by', {})

                    results.append({
                        'title': result.get('title', ''),
                        'url': result.get('link', ''),
                        'description': result.get('snippet', 'No description available'),
                        'authors': pub_info.get('summary', ''),
                        'year': '',
                        'citations': cited_by.get('total', 0) if cited_by else 0,
                        'venue': '',
                        'source': 'Google Scholar'
                    })

            return results
        else:
            print(f"SerpAPI error: {response.status_code}")
            return []

    except Exception as e:
        print(f"Google Scholar search error: {e}")
        return []