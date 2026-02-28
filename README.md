# InterviewIQ 🚀

AI-powered Interview Preparation & Job Description Matcher

## Features
- 📋 **JD Analyzer** — Extracts skills, topics & likely interview questions from any job description
- 🎯 **Resume Matcher** — Scores your resume against a JD, finds gaps & gives recommendations
- 📚 **Interview Prep Plan** — Generates a personalized study plan with resources
- 🎤 **Mock Interview** — AI-powered mock interview with real-time feedback

## Tech Stack
- **Frontend:** Pure HTML/CSS/JS (Iron Man dark theme)
- **Backend:** FastAPI + Python
- **AI:** Groq (LLaMA 3.3 70B) — Free & fast

## Deployment

### Backend (Render)
1. Connect this repo to [Render](https://render.com)
2. Root directory: `backend`
3. Build: `pip install -r requirements.txt`
4. Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add env vars:
   - `OPENAI_API_KEY` = your Groq API key
   - `OPENAI_BASE_URL` = `https://api.groq.com/openai/v1`
   - `AI_MODEL` = `llama-3.3-70b-versatile`

### Frontend
Update `const API` in `frontend/index.html` to your Render backend URL, then deploy to any static host.

## Live Demo
Coming soon!

---
Built with ❤️ by Jarvis AI
