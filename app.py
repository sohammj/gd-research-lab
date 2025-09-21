#!/usr/bin/env python3
"""
Gemini Link Search - Enhanced API Version
Main entry point for the CLI interface.
"""
import os
import sys
import time
from dotenv import load_dotenv
import google.generativeai as genai
from gemini import analyze_prompt_with_gemini, print_analysis
from gitkag import search_github_api, search_kaggle
from forum import search_reddit_api, search_medium, search_quora
from scholar import search_semantic_scholar, search_google_scholar_serpapi
from summarizer import print_results

load_dotenv()

# Configure API Keys
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'LinkSearchBot/1.0')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
SEMANTIC_SCHOLAR_API_KEY = os.getenv('SEMANTIC_SCHOLAR_API_KEY')
SERPAPI_KEY = os.getenv('SERPAPI_KEY')
KAGGLE_USERNAME = os.getenv('KAGGLE_USERNAME')
KAGGLE_KEY = os.getenv('KAGGLE_KEY')

# Check required API keys
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not set. Please set it as environment variable.")
    print("Example: export GEMINI_API_KEY='your-api-key-here'")
    sys.exit(1)

# Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def show_api_status():
    """Display the status of all configured APIs"""
    print("API CONFIGURATION STATUS:")
    print("-" * 50)

    # Required APIs
    print(f"   Gemini AI: Configured")

    # Optional APIs
    apis = [
        ("Reddit", REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET),
        ("GitHub", GITHUB_TOKEN),
        ("Kaggle", KAGGLE_USERNAME and KAGGLE_KEY),
        ("Semantic Scholar", SEMANTIC_SCHOLAR_API_KEY),
        ("Google Scholar (SerpAPI)", SERPAPI_KEY),
        ("Medium (Scraping)", True),
        ("Quora (Scraping)", True)
    ]

    for name, configured in apis:
        status = "Configured" if configured else "Not configured"
        print(f"   {status}: {name}")

    configured_count = sum(1 for _, configured in apis if configured) + 1
    print(f"\n  Total APIs configured: {configured_count}/7")
    print()

def search_for_links(prompt):
    """Main function to search for links across all platforms"""
    print(f"\nSearching for: '{prompt}'")

    # Step 1: Analyze with Gemini
    analysis = analyze_prompt_with_gemini(prompt, model)
    print_analysis(analysis)

    # Step 2: Search across multiple platforms
    print("\nSearching across multiple platforms...")
    all_results = []
    search_count = 0

    # Get search terms from analysis
    reddit_queries = analysis.get('reddit_queries', analysis.get('search_terms', [prompt]))[:2]
    github_queries = analysis.get('github_queries', [prompt])[:2]
    kaggle_queries = analysis.get('kaggle_queries', [prompt])[:2]
    medium_queries = analysis.get('medium_queries', [prompt])[:2]
    quora_queries = analysis.get('quora_queries', [prompt])[:2]
    academic_terms = analysis.get('academic_terms', [prompt])[:2]

    # Search Reddit
    if REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET:
        print("Searching Reddit...")
        for query in reddit_queries:
            reddit_results = search_reddit_api(query, 4)
            all_results.extend(reddit_results)
            search_count += 1
            time.sleep(1)
    else:
        print("Skipping Reddit (API credentials not configured)")

    # Search GitHub
    print("Searching GitHub...")
    for query in github_queries:
        github_results = search_github_api(query, 5)
        all_results.extend(github_results)
        search_count += 1
        time.sleep(1)

    # Search Kaggle
    if KAGGLE_USERNAME and KAGGLE_KEY:
        print("Searching Kaggle...")
        for query in kaggle_queries:
            kaggle_results = search_kaggle(query, 4)
            all_results.extend(kaggle_results)
            search_count += 1
            time.sleep(1)
    else:
        print("Skipping Kaggle (API credentials not configured)")

    # Search Medium
    print("Searching Medium...")
    for query in medium_queries:
        medium_results = search_medium(query, 4)
        all_results.extend(medium_results)
        search_count += 1
        time.sleep(1)

    # Search Quora
    print("Searching Quora...")
    for query in quora_queries:
        quora_results = search_quora(query, 4)
        all_results.extend(quora_results)
        search_count += 1
        time.sleep(1)

    # Search Semantic Scholar
    if SEMANTIC_SCHOLAR_API_KEY:
        print("Searching Semantic Scholar...")
        for term in academic_terms:
            scholar_results = search_semantic_scholar(term, 4)
            all_results.extend(scholar_results)
            search_count += 1
            time.sleep(1)
    else:
        print("Skipping Semantic Scholar (API key not configured)")

    # Search Google Scholar via SerpAPI
    if SERPAPI_KEY:
        print("Searching Google Scholar...")
        for term in academic_terms:
            gs_results = search_google_scholar_serpapi(term, 4)
            all_results.extend(gs_results)
            search_count += 1
            time.sleep(1)
    else:
        print("Skipping Google Scholar (SerpAPI key not configured)")

    print(f"Completed {search_count} API calls")

    # Step 3: Remove duplicates and filter
    seen_urls = set()
    unique_results = []

    for result in all_results:
        url = result.get('url', '')
        if url and url not in seen_urls and len(url) > 10:
            seen_urls.add(url)
            unique_results.append(result)

    # Step 4: Sort results by relevance/quality
    def sort_key(result):
        source = result.get('source', '')
        if source == 'GitHub':
            return result.get('stars', 0)
        elif source == 'Reddit':
            return result.get('score', 0)
        elif source == 'Kaggle':
            return result.get('votes', 0)
        elif source in ['Semantic Scholar', 'Google Scholar']:
            return result.get('citations', 0)
        return 0

    unique_results.sort(key=sort_key, reverse=True)

    # Step 5: Show results (limit to top 30)
    final_results = unique_results[:30]
    print_results(final_results)

    return final_results

def main():
    """Main CLI interface"""
    print("GEMINI LINK SEARCH - ENHANCED API VERSION")
    print("=" * 70)
    print("AI-powered link discovery across multiple premium platforms")
    print("Sources: Reddit • GitHub • Kaggle • Semantic Scholar • Google Scholar • Medium • Quora")
    print("=" * 70)

    # Show API status
    show_api_status()

    print("Tips:")
    print("   Be specific in your prompts for better results")
    print("   Academic topics work best for research papers")
    print("   Technical topics will show more GitHub repositories")
    print("   Type 'quit', 'exit', or 'q' to stop\n")

    search_number = 1

    while True:
        try:
            # Get user input
            prompt = input(f"[{search_number}] Enter your search prompt: ").strip()

            # Check for exit commands
            if prompt.lower() in ['quit', 'exit', 'q', 'stop']:
                print("\nThank you for using Gemini Link Search!")
                break

            # Check for empty input
            if not prompt:
                print("Please enter a search prompt.")
                continue

            # Record start time
            start_time = time.time()

            # Search for links
            results = search_for_links(prompt)

            # Show summary
            end_time = time.time()
            duration = end_time - start_time

            print(f"\nSEARCH SUMMARY:")
            print(f"   Search completed in {duration:.1f} seconds")
            print(f"   Found {len(results)} unique links")
            print(f"   Query: '{prompt}'")

            # Ask if user wants to continue
            print("\n" + "="*70)
            continue_search = input("Search again? (y/n/help): ").strip().lower()

            if continue_search in ['n', 'no']:
                print("\nThank you for using Gemini Link Search!")
                break
            elif continue_search in ['help', 'h']:
                print("\nUSAGE TIPS:")
                print("   Try: 'machine learning tutorials'")
                print("   Try: 'react components github'")
                print("   Try: 'climate change research papers'")
                print("   Try: 'python web scraping reddit discussion'")
                print()
            else:
                search_number += 1
                print()

        except KeyboardInterrupt:
            print("\n\nSearch interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")
            print("Please try again with a different search term.")
            continue

if __name__ == "__main__":
    main()