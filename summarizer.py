def print_results(results):
    """Print search results in a nice format"""
    if not results:
        print("\nNo results found.")
        return

    print(f"\n" + "="*80)
    print(f"FOUND {len(results)} RELEVANT LINKS")
    print("="*80)

    # Group by source
    by_source = {}
    for result in results:
        source = result.get('source', 'Unknown')
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(result)

    # Print results by source
    for source, source_results in by_source.items():
        if source_results:
            print(f"\n{source.upper()} ({len(source_results)} results)")
            print("-" * 60)

            for i, result in enumerate(source_results, 1):
                title = result.get('title', 'No title')
                if len(title) > 70:
                    title = title[:67] + "..."

                url = result.get('url', '')
                description = result.get('description', '')
                if len(description) > 120:
                    description = description[:117] + "..."

                print(f"{i}. {title}")
                print(f"   {url}")

                if description and description.strip():
                    print(f"   {description}")

                # Add source-specific metadata
                if source == 'GitHub':
                    stars = result.get('stars', 0)
                    language = result.get('language', '')
                    forks = result.get('forks', 0)
                    metadata = f"{stars:,} stars"
                    if forks:
                        metadata += f" | {forks:,} forks"
                    if language and language != 'Unknown':
                        metadata += f" | {language}"
                    print(f"   {metadata}")

                elif source == 'Reddit':
                    subreddit = result.get('subreddit', '')
                    score = result.get('score', 0)
                    comments = result.get('comments', 0)
                    print(f"   r/{subreddit} | {score:,} points | {comments:,} comments")

                elif source == 'Kaggle':
                    votes = result.get('votes', 0)
                    print(f"   {votes:,} votes")

                elif source in ['Semantic Scholar', 'Google Scholar']:
                    year = result.get('year', '')
                    citations = result.get('citations', 0)
                    authors = result.get('authors', '')
                    venue = result.get('venue', '')

                    metadata_parts = []
                    if year and year != 'Unknown':
                        metadata_parts.append(f"{year}")
                    if citations > 0:
                        metadata_parts.append(f"{citations:,} citations")
                    if venue and venue != 'Unknown':
                        metadata_parts.append(f"{venue}")

                    if metadata_parts:
                        print(f"   {' | '.join(metadata_parts)}")

                    if authors and len(authors) > 10:
                        authors_display = authors[:60] + "..." if len(authors) > 60 else authors
                        print(f"   {authors_display}")

                print()