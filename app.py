from flask import Flask, render_template, request, jsonify, session
import google.generativeai as genai
from autogen import ConversableAgent
import json
import os
import asyncio
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Global variable to store API key (in production, use environment variables)
GEMINI_API_KEY = None

def create_gemini_agent(name, system_message, api_key):
    """Create a simple AutoGen agent powered by Gemini"""
    
    # Configure Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Create the agent
    agent = ConversableAgent(
        name=name,
        system_message=system_message,
        llm_config=False,
        human_input_mode="NEVER"
    )
    
    # Override the generate_reply method
    def gemini_reply(messages=None, sender=None, **kwargs):
        if not messages:
            return f"{name}: No message to process"
        
        # Get the last message
        last_msg = messages[-1]["content"] if isinstance(messages[-1], dict) else str(messages[-1])
        
        # Create prompt
        prompt = f"{system_message}\n\nTask: {last_msg}"
        
        try:
            response = model.generate_content(prompt)
            return response.text if response.text else f"{name}: Could not generate response"
        except Exception as e:
            return f"{name}: Error - {str(e)}"
    
    agent.generate_reply = gemini_reply
    return agent

def analyze_research_idea(title, description, domain, gemini_api_key):
    """Analyze research idea using AutoGen multi-agent system"""
    
    # Create the 5 specialist agents
    agents_config = {
        "CritiqueExpert": """You are a research critique expert. Analyze the research idea and provide:
SCORE: [1-10 rating based on novelty, feasibility, impact]
ANALYSIS: [Critical analysis - be objective, not just agreeable]
GAPS: [Key weaknesses or gaps you identify]
SUGGESTIONS: [Specific improvements needed]
🔹 1. Novelty (Originality of Idea)
Indicators:
Literature overlap:
If many papers exist with very similar titles/keywords → novelty ↓.
If only adjacent or tangential work exists → novelty ↑.

Method uniqueness:
Using the same standard models (e.g., CNN for DR detection) → lower.
New dataset, population, or modality → higher.

Setting:
Applying existing methods in a new domain/context counts as modest novelty.

Score Guide (0–100):
0–40 = crowded, done many times.
40–70 = incremental but still useful.
70–100 = genuinely underexplored, fresh angle.


🔹 2. Feasibility (Can it actually be done?)
Indicators:
Data availability:
Public datasets exist (ImageNet, UCI, PubMed, etc.) → feasibility ↑.
Requires sensitive/expensive/private data → feasibility ↓.

Resources & tools:
Established toolkits/libraries available → ↑.
Needs special hardware, labs, or licensing → ↓.

Complexity vs. skills:
A PhD-level challenge with no prior baseline → low feasibility.
Well-scoped with clear roadmap → high feasibility.

Score Guide:
0–40 = unrealistic without major funding.
40–70 = doable but with obstacles.
70–100 = straightforward with existing resources.

🔹 3. Impact (Why does it matter?)
Indicators:
Social benefit:
Education, health, climate, safety, or accessibility → big ↑.
Scale:
Affects millions (policy, global health) → ↑.
Niche with little wider application → ↓.


Adoption potential:Could be integrated into real workflows (apps, clinics, gov) → ↑.
Longevity:
Solves a persistent problem (e.g., clean water, energy efficiency) → ↑.
Score Guide:
0–40 = low impact / academic exercise only.
40–70 = useful for a sub-community.
70–100 = transformative if successful.

🔹 4. Gap Indicators (for critique narrative)
When the model critiques, it should also list:
Missing data: “No longitudinal studies in rural areas.”
Missing methods: “Lacks qualitative evaluation alongside quantitative.”
Missing populations: “No results for low-income countries.”
Missing evaluations: “No ablation studies / reproducibility checks.”


These make the critique specific, not generic.

🔹 Example Critique Output
Novelty (65):
Many works on diabetic retinopathy detection using CNNs.
Few address smartphone-based fundus images in low-resource settings.
Gap: lack of large-scale comparative benchmarks.


Feasibility (75):
Public datasets exist for DR but limited smartphone data.
Tools like PyTorch + pre-trained vision models available.
Hardware constraints (low-cost cameras) could be challenging.


Impact (85):
Could democratize screening in low-income countries.
High relevance to global health.
Strong adoption potential if validated clinically.
""",
        
        "ExpansionSpecialist": """You are a research expansion expert. Help expand the research idea:
RESEARCH_QUESTIONS: [Specific questions to investigate]
NICHES: [Potential specialized areas to focus on]
METHODOLOGIES: [Research approaches to consider]
TRENDS: [How this connects to current trends]""",
        
        "GapFinder": """You are a research gap identification expert. Find opportunities:
MAJOR_GAPS: [Significant unexplored areas in this domain]
EMERGING_TRENDS: [New areas needing research attention]
OPPORTUNITIES: [Cross-disciplinary possibilities]""",
        
        "ResourceLibrarian": """You are a research resource expert. Suggest resources:
KEY_PAPERS: [Important papers to read in this area]
DATASETS: [Relevant datasets available]
TOOLS: [Software/platforms that could be useful]
VENUES: [Conferences and journals for this research]""",
        
        "ResearchPlanner": """You are a research planning expert. Create an action plan:
NEXT_STEPS: [Prioritized action items]
TIMELINE: [Realistic milestone schedule]
CHALLENGES: [Potential obstacles and solutions]
SUCCESS_METRICS: [How to measure progress]"""
    }
    
    # The research query
    research_query = f"""
RESEARCH IDEA:
Title: {title}
Description: {description}
Domain: {domain}

Please analyze this research idea according to your expertise.
"""
    
    # Get responses from each agent
    results = {
        "title": title,
        "description": description,
        "domain": domain,
        "timestamp": datetime.now().isoformat(),
        "agent_responses": {}
    }
    
    for agent_name, system_message in agents_config.items():
        try:
            agent = create_gemini_agent(agent_name, system_message, gemini_api_key)
            response = agent.generate_reply([{"content": research_query}])
            results["agent_responses"][agent_name] = response
        except Exception as e:
            results["agent_responses"][agent_name] = f"Error: {str(e)}"
    
    return results

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/set-key', methods=['POST'])
def set_api_key():
    """Set the Gemini API key"""
    global GEMINI_API_KEY
    
    data = request.get_json()
    api_key = data.get('api_key', '').strip()
    
    if not api_key:
        return jsonify({"success": False, "message": "API key is required"})
    
    # Test the API key
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Hello")
        
        if response.text:
            GEMINI_API_KEY = api_key
            session['api_key_set'] = True
            return jsonify({"success": True, "message": "API key validated and set!"})
        else:
            return jsonify({"success": False, "message": "Invalid API key - no response from Gemini"})
            
    except Exception as e:
        return jsonify({"success": False, "message": f"API key validation failed: {str(e)}"})

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Analyze research idea endpoint"""
    global GEMINI_API_KEY
    
    if not GEMINI_API_KEY:
        return jsonify({"success": False, "message": "Please set your Gemini API key first"})
    
    data = request.get_json()
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    domain = data.get('domain', '').strip()
    
    # Validate input
    if not all([title, description, domain]):
        return jsonify({"success": False, "message": "All fields (title, description, domain) are required"})
    
    try:
        # Analyze the research idea
        results = analyze_research_idea(title, description, domain, GEMINI_API_KEY)
        
        # Store in session for potential download
        session_id = str(uuid.uuid4())
        session[f'results_{session_id}'] = results
        
        return jsonify({
            "success": True, 
            "results": results,
            "session_id": session_id,
            "message": "Analysis completed successfully!"
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Analysis failed: {str(e)}"})

@app.route('/api/download/<session_id>')
def download_results(session_id):
    """Download results as JSON"""
    results = session.get(f'results_{session_id}')
    
    if not results:
        return jsonify({"error": "Results not found"}), 404
    
    response = app.response_class(
        response=json.dumps(results, indent=2),
        status=200,
        mimetype='application/json'
    )
    response.headers['Content-Disposition'] = f'attachment; filename=research_analysis_{results["title"].replace(" ", "_")}.json'
    
    return response

@app.route('/history')
def history():
    """Show analysis history"""
    return render_template('history.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)