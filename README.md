
🧠 GD Research Lab – AI Research Mentor
🚩 Problem Statement

LLMs (like ChatGPT) often agree with users instead of critiquing.

They act like generalists, not true domain experts.

Most learners don’t have access to research mentors who can guide them through:

spotting gaps

understanding history of research

analyzing trends

structuring ideas

👉 Our Solution: An AI research mentor that challenges ideas, finds gaps, and guides next steps.

🔄 Main Workflow

User Input (chat/voice)

Enter an idea or research topic.

Or say “I don’t know where to start” → system helps find a niche.

AI Critique + Score

Cluster analysis (compare with existing research areas).

Gap finding (what’s missing in the field).

Novelty, feasibility, and impact scores.

Expansion

If vague → refine the idea.

If clear → suggest niche directions.

Resource Mining

Fetch & summarize relevant research papers (arXiv, Semantic Scholar, Gemini).

Pull citations and basic visual trends.

Next Steps Generator

Suggest paper outline (IMRaD).

Key points, methodology, and template for writing.

💬 Modes of Input

Chatbot (text)

Voice bot (real-time with LiveKit)

🛠 Tech Stack

Backend AI

python-autogen
 (multi-agent reasoning)

Gemini / OpenAI APIs for LLM reasoning

arXiv & Semantic Scholar APIs for research papers

Frontend

React + Next.js (dashboard UI)

Tailwind / Chakra UI for components

Voice

LiveKit for real-time interaction

Data Handling

FastAPI / Flask (API endpoints)

SQLite (MVP) → Postgres (scalable)

Deployment

Vercel (frontend)

Render / Heroku (backend)

⚡ Hackathon MVP Scope

Core Features

Input a research idea → get novelty & feasibility scores.

AI suggests 2–3 research gaps.

Dashboard displays results.

Stretch Goals

Fetch 2–3 related papers (Semantic Scholar API).

Auto-generate research outline.

Add voice interaction (“mentor bot” demo).

This version sells your problem → solution → stack → scope cleanly to anyone landing on your repo.
