#!/usr/bin/env python3
"""
Gemini Link Search - Enhanced API Version
Main entry point for the CLI interface.
"""
import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path
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

def collect_research_input():
    """
    Function 1: Collect research topic, description, and input files from user
    """
    print("\nRESEARCH PROJECT SETUP")
    print("=" * 50)
    
    # Get research topic
    topic = input("Enter your research topic: ").strip()
    if not topic:
        print("Error: Research topic is required.")
        return None
    
    # Get research description
    print("\nEnter a detailed description of your research:")
    print("(Press Enter twice when finished)")
    description_lines = []
    while True:
        line = input()
        if line == "" and description_lines and description_lines[-1] == "":
            break
        description_lines.append(line)
    
    description = "\n".join(description_lines).strip()
    if not description:
        print("Error: Research description is required.")
        return None
    
    # Get input files (optional)
    input_files = []
    while True:
        file_path = input("\nEnter path to input file (or press Enter to skip): ").strip()
        if not file_path:
            break
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                input_files.append({
                    'path': file_path,
                    'name': os.path.basename(file_path),
                    'content': content[:5000]  # Limit content length
                })
                print(f"✓ Added: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
        else:
            print(f"File not found: {file_path}")
    
    research_data = {
        'topic': topic,
        'description': description,
        'input_files': input_files,
        'timestamp': datetime.now().isoformat()
    }
    
    print(f"\n✓ Research setup complete:")
    print(f"  Topic: {topic}")
    print(f"  Description: {len(description)} characters")
    print(f"  Input files: {len(input_files)}")
    
    return research_data

def critique_research_proposal(research_data, model):
    """
    Function 2: Use Gemini to brutally critique the research idea with expert scoring
    """
    print("\nRESEARCH PROPOSAL CRITIQUE")
    print("=" * 50)
    
    # Prepare input files content
    files_content = ""
    if research_data['input_files']:
        files_content = "\n\nInput Files Content:\n"
        for file_info in research_data['input_files']:
            files_content += f"\n--- {file_info['name']} ---\n{file_info['content']}\n"
    
    critique_prompt = f"""
    Act as an expert research committee evaluating a research proposal. Provide a brutal, honest critique using standard academic evaluation criteria.
    
    RESEARCH PROPOSAL:
    Topic: {research_data['topic']}
    
    Description:
    {research_data['description']}
    {files_content}
    
    EVALUATION CRITERIA (Score 1-10 for each):
    
    1. NOVELTY & ORIGINALITY (1-10)
       - Is this research novel and original?
       - Does it contribute new knowledge to the field?
    
    2. SIGNIFICANCE & IMPACT (1-10)
       - Will this research have significant impact?
       - Is it addressing an important problem?
    
    3. FEASIBILITY & METHODOLOGY (1-10)
       - Is the research feasible with current resources/methods?
       - Are the proposed methods sound?
    
    4. LITERATURE FOUNDATION (1-10)
       - Is there sufficient background understanding?
       - How well does it build on existing work?
    
    5. CLARITY & SCOPE (1-10)
       - Is the research question clearly defined?
       - Is the scope appropriate?
    
    6. POTENTIAL FOR SUCCESS (1-10)
       - What's the likelihood of successful completion?
       - Are the goals realistic?
    
    Provide your response in this JSON format:
    {{
        "overall_score": [total score out of 60],
        "grade": ["Excellent", "Good", "Fair", "Poor", "Reject"],
        "scores": {{
            "novelty": [1-10],
            "significance": [1-10],
            "feasibility": [1-10],
            "literature": [1-10],
            "clarity": [1-10],
            "success_potential": [1-10]
        }},
        "strengths": ["list of 3-5 key strengths"],
        "weaknesses": ["list of 3-5 critical weaknesses"],
        "recommendations": ["list of 3-5 specific improvement recommendations"],
        "brutal_feedback": "[2-3 paragraphs of honest, direct critique]",
        "verdict": "[Accept/Minor Revisions/Major Revisions/Reject with clear reasoning]"
    }}
    
    Be brutally honest. Don't sugarcoat. Point out real problems and limitations.
    """
    
    try:
        print("Analyzing research proposal with expert critique...")
        response = model.generate_content(critique_prompt)
        response_text = response.text.strip()
        
        # Clean JSON response
        if response_text.startswith('```json'):
            response_text = response_text[7:-3]
        elif response_text.startswith('```'):
            response_text = response_text[3:-3]
        
        critique = json.loads(response_text)
        
        # Display critique results
        print(f"\n🔥 EXPERT CRITIQUE RESULTS 🔥")
        print(f"Overall Score: {critique['overall_score']}/60 ({critique['grade']})")
        print(f"Verdict: {critique['verdict']}")
        
        print("\nDETAILED SCORES:")
        for category, score in critique['scores'].items():
            print(f"  {category.replace('_', ' ').title()}: {score}/10")
        
        print("\n✅ STRENGTHS:")
        for strength in critique['strengths']:
            print(f"  • {strength}")
        
        print("\n❌ CRITICAL WEAKNESSES:")
        for weakness in critique['weaknesses']:
            print(f"  • {weakness}")
        
        print("\n📝 RECOMMENDATIONS:")
        for rec in critique['recommendations']:
            print(f"  • {rec}")
        
        print("\n🔥 BRUTAL FEEDBACK:")
        print(f"  {critique['brutal_feedback']}")
        
        return critique
        
    except Exception as e:
        print(f"Error during critique: {e}")
        return None

def collect_research_resources(research_data, model):
    """
    Function 3: Run all existing functions to gather resources and store in JSON
    """
    print("\nCOLLECTING RESEARCH RESOURCES")
    print("=" * 50)
    
    try:
        # Use existing search_for_links function to gather all resources
        search_query = f"{research_data['topic']} {research_data['description'][:200]}"
        print(f"Searching for resources related to: {search_query[:100]}...")
        
        # Gather all resources using existing function
        resources = search_for_links(search_query)
        
        # Organize resources by source
        organized_resources = {
            'papers': [],
            'datasets': [],
            'code_repos': [],
            'discussions': [],
            'articles': [],
            'other': []
        }
        
        for resource in resources:
            source = resource.get('source', '').lower()
            if source in ['semantic scholar', 'google scholar']:
                organized_resources['papers'].append(resource)
            elif source == 'kaggle':
                organized_resources['datasets'].append(resource)
            elif source == 'github':
                organized_resources['code_repos'].append(resource)
            elif source == 'reddit':
                organized_resources['discussions'].append(resource)
            elif source in ['medium', 'quora']:
                organized_resources['articles'].append(resource)
            else:
                organized_resources['other'].append(resource)
        
        # Create comprehensive research package
        research_package = {
            'research_info': research_data,
            'resources': organized_resources,
            'collection_timestamp': datetime.now().isoformat(),
            'total_resources': len(resources),
            'resource_counts': {key: len(value) for key, value in organized_resources.items()}
        }
        
        # Save to JSON file
        filename = f"research_resources_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(research_package, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ RESOURCES COLLECTED AND SAVED")
        print(f"File: {filename}")
        print(f"Total resources: {len(resources)}")
        for category, count in research_package['resource_counts'].items():
            if count > 0:
                print(f"  {category.replace('_', ' ').title()}: {count}")
        
        return research_package
        
    except Exception as e:
        print(f"Error collecting resources: {e}")
        return None

def analyze_research_direction(research_package, model):
    """
    Function 4: Use Gemini to analyze collected data and provide focused research direction
    """
    print("\nANALYZING RESEARCH DIRECTION")
    print("=" * 50)
    
    # Prepare resource summaries for analysis
    resource_summary = "\n\nCOLLECTED RESOURCES SUMMARY:\n"
    
    for category, resources in research_package['resources'].items():
        if resources:
            resource_summary += f"\n{category.upper()} ({len(resources)} items):\n"
            for i, resource in enumerate(resources[:5]):
                title = resource.get('title', 'No title')[:100]
                desc = resource.get('description', 'No description')[:200]
                resource_summary += f"  {i+1}. {title}\n     {desc}\n"
            if len(resources) > 5:
                resource_summary += f"     ... and {len(resources) - 5} more\n"
    
    direction_prompt = f"""
    Act as a senior research advisor analyzing collected resources to provide expert direction for a research project.
    
    ORIGINAL RESEARCH PROPOSAL:
    Topic: {research_package['research_info']['topic']}
    Description: {research_package['research_info']['description']}
    
    {resource_summary}
    
    Based on the collected resources and current research landscape, provide a comprehensive research direction analysis in JSON format:
    
    {{
        "refined_research_focus": "[Specific, refined research question/focus based on gap analysis]",
        "research_niche": "[Exact niche this research should target]",
        "key_gaps_identified": ["list of 3-5 specific gaps in current literature"],
        "methodological_approach": "[Recommended research methodology and approach]",
        "expected_contributions": ["list of 3-4 specific expected contributions"],
        "research_timeline": {{
            "phase_1": "[Timeline and activities for phase 1]",
            "phase_2": "[Timeline and activities for phase 2]",
            "phase_3": "[Timeline and activities for phase 3]"
        }},
        "key_papers_to_review": ["list of 5-7 most important papers from collected resources"],
        "datasets_to_use": ["list of relevant datasets from collected resources"],
        "collaboration_opportunities": ["potential collaboration areas based on resources"],
        "risk_assessment": ["list of 3-4 potential risks and mitigation strategies"],
        "success_metrics": ["list of 3-4 concrete success metrics"],
        "next_immediate_steps": ["list of 5-7 immediate actionable steps"]
    }}
    
    Provide highly specific, actionable direction based on the actual resources collected.
    """
    
    try:
        print("Analyzing research direction with expert guidance...")
        response = model.generate_content(direction_prompt)
        response_text = response.text.strip()
        
        # Clean JSON response
        if response_text.startswith('```json'):
            response_text = response_text[7:-3]
        elif response_text.startswith('```'):
            response_text = response_text[3:-3]
        
        direction_analysis = json.loads(response_text)
        
        # Display direction analysis
        print(f"\n🎯 EXPERT RESEARCH DIRECTION")
        print(f"\n🔬 REFINED FOCUS:")
        print(f"  {direction_analysis['refined_research_focus']}")
        
        print(f"\n🎪 RESEARCH NICHE:")
        print(f"  {direction_analysis['research_niche']}")
        
        print(f"\n🔍 KEY GAPS IDENTIFIED:")
        for gap in direction_analysis['key_gaps_identified']:
            print(f"  • {gap}")
        
        print(f"\n📋 METHODOLOGICAL APPROACH:")
        print(f"  {direction_analysis['methodological_approach']}")
        
        print(f"\n🏆 EXPECTED CONTRIBUTIONS:")
        for contrib in direction_analysis['expected_contributions']:
            print(f"  • {contrib}")
        
        print(f"\n📅 RESEARCH TIMELINE:")
        for phase, activities in direction_analysis['research_timeline'].items():
            print(f"  {phase.upper()}: {activities}")
        
        print(f"\n🚀 IMMEDIATE NEXT STEPS:")
        for step in direction_analysis['next_immediate_steps']:
            print(f"  • {step}")
        
        return direction_analysis
        
    except Exception as e:
        print(f"Error analyzing research direction: {e}")
        return None

def generate_research_paper_template(research_package, direction_analysis, model):
    """
    Function 5: Generate a paper template and draft based on research direction
    """
    print("\nGENERATING RESEARCH PAPER TEMPLATE")
    print("=" * 50)
    
    template_prompt = f"""
    Create a comprehensive research paper template and initial draft based on the research direction analysis.
    
    RESEARCH DETAILS:
    Topic: {research_package['research_info']['topic']}
    Refined Focus: {direction_analysis['refined_research_focus']}
    Niche: {direction_analysis['research_niche']}
    Methodology: {direction_analysis['methodological_approach']}
    
    Generate a complete paper template with initial content in the following structure:
    
    {{
        "title": "[Proposed paper title]",
        "abstract": "[150-200 word abstract draft]",
        "keywords": ["list of 5-7 relevant keywords"],
        "sections": {{
            "1_introduction": {{
                "title": "Introduction",
                "content": "[Draft introduction content with problem statement, motivation, and objectives]",
                "subsections": ["list of subsection titles"]
            }},
            "2_literature_review": {{
                "title": "Literature Review",
                "content": "[Draft literature review structure and key points]",
                "subsections": ["list of subsection titles"]
            }},
            "3_methodology": {{
                "title": "Methodology",
                "content": "[Draft methodology description]",
                "subsections": ["list of subsection titles"]
            }},
            "4_results": {{
                "title": "Results and Analysis",
                "content": "[Expected results structure]",
                "subsections": ["list of subsection titles"]
            }},
            "5_discussion": {{
                "title": "Discussion",
                "content": "[Discussion framework]",
                "subsections": ["list of subsection titles"]
            }},
            "6_conclusion": {{
                "title": "Conclusion and Future Work",
                "content": "[Conclusion structure]",
                "subsections": ["list of subsection titles"]
            }}
        }},
        "figures_tables": ["list of proposed figures and tables"],
        "reference_framework": ["structure for organizing references from collected resources"]
    }}
    
    Create substantial draft content for each section, not just placeholders.
    """
    
    try:
        print("Generating research paper template and draft...")
        response = model.generate_content(template_prompt)
        response_text = response.text.strip()
        
        # Clean JSON response
        if response_text.startswith('```json'):
            response_text = response_text[7:-3]
        elif response_text.startswith('```'):
            response_text = response_text[3:-3]
        
        paper_template = json.loads(response_text)
        
        # Create paper document
        paper_content = f"""# {paper_template['title']}

## Abstract
{paper_template['abstract']}

**Keywords:** {', '.join(paper_template['keywords'])}

"""
        
        # Add sections
        for section_key, section_data in paper_template['sections'].items():
            section_num = section_key.split('_')[0]
            paper_content += f"\n## {section_num}. {section_data['title']}\n\n"
            paper_content += f"{section_data['content']}\n\n"
            
            if section_data.get('subsections'):
                for i, subsection in enumerate(section_data['subsections'], 1):
                    paper_content += f"### {section_num}.{i} {subsection}\n\n[Content to be developed]\n\n"
        
        # Add figures and tables section
        if paper_template.get('figures_tables'):
            paper_content += "\n## Figures and Tables\n\n"
            for item in paper_template['figures_tables']:
                paper_content += f"- {item}\n"
        
        # Save paper template
        paper_filename = f"research_paper_draft_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(paper_filename, 'w', encoding='utf-8') as f:
            f.write(paper_content)
        
        # Save template JSON
        template_filename = f"paper_template_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(template_filename, 'w', encoding='utf-8') as f:
            json.dump(paper_template, f, indent=2, ensure_ascii=False)
        
        print(f"\n📝 RESEARCH PAPER GENERATED")
        print(f"\n📄 TITLE: {paper_template['title']}")
        print(f"\n📁 FILES CREATED:")
        print(f"  • Paper Draft: {paper_filename}")
        print(f"  • Template JSON: {template_filename}")
        
        print(f"\n📋 PAPER STRUCTURE:")
        for section_key, section_data in paper_template['sections'].items():
            section_num = section_key.split('_')[0]
            print(f"  {section_num}. {section_data['title']}")
            if section_data.get('subsections'):
                for i, subsection in enumerate(section_data['subsections'], 1):
                    print(f"    {section_num}.{i} {subsection}")
        
        return {
            'template': paper_template,
            'paper_file': paper_filename,
            'template_file': template_filename
        }
        
    except Exception as e:
        print(f"Error generating paper template: {e}")
        return None

def research_assistant_workflow():
    """
    Main workflow function that orchestrates all research assistant functions
    """
    print("\n🔬 AI RESEARCH ASSISTANT WORKFLOW")
    print("=" * 70)
    print("Complete research workflow: Input → Critique → Resources → Direction → Paper")
    print("=" * 70)
    
    try:
        # Step 1: Collect research input
        research_data = collect_research_input()
        if not research_data:
            return
        
        # Step 2: Critique the research proposal
        critique = critique_research_proposal(research_data, model)
        if not critique:
            return
        
        # Check if critique is too negative to continue
        if critique['overall_score'] < 25:  # Less than 25/60
            print(f"\n⚠️ WARNING: Research proposal received low score ({critique['overall_score']}/60)")
            continue_choice = input("Continue with resource collection anyway? (y/n): ").strip().lower()
            if continue_choice != 'y':
                print("Research workflow stopped. Please revise your proposal and try again.")
                return
        
        # Step 3: Collect research resources
        research_package = collect_research_resources(research_data, model)
        if not research_package:
            return
        
        # Step 4: Analyze research direction
        direction_analysis = analyze_research_direction(research_package, model)
        if not direction_analysis:
            return
        
        # Step 5: Generate paper template
        paper_result = generate_research_paper_template(research_package, direction_analysis, model)
        if not paper_result:
            return
        
        # Final summary
        print("\n" + "=" * 70)
        print("🎉 RESEARCH WORKFLOW COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print(f"Research Topic: {research_data['topic']}")
        print(f"Critique Score: {critique['overall_score']}/60 ({critique['grade']})")
        print(f"Resources Collected: {research_package['total_resources']}")
        print(f"Paper Draft: {paper_result['paper_file']}")
        print("\nAll files have been saved to your current directory.")
        print("You can now proceed with your research based on the expert guidance provided!")
        
    except Exception as e:
        print(f"Error in research workflow: {e}")

if __name__ == "__main__":
    # Check if user wants research workflow or regular link search
    print("\nSELECT MODE:")
    print("1. 🔬 Research Assistant Workflow (New!)")
    print("2. 🔍 Regular Link Search")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == '1':
        research_assistant_workflow()
    else:
        main()