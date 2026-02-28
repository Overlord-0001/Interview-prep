from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import json, re, os

app = FastAPI(title="InterviewIQ API", version="1.1")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

API_BASE = os.environ.get("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")
API_KEY  = os.environ.get("OPENAI_API_KEY", "")
MODEL    = os.environ.get("AI_MODEL", "llama-3.3-70b-versatile")

client = OpenAI(base_url=API_BASE, api_key=API_KEY)

def chat(prompt: str, system: str = "You are an expert AI career coach and technical interviewer. Always return valid JSON when asked.") -> str:
    res = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        max_tokens=2048,
        temperature=0.7
    )
    return res.choices[0].message.content

def parse_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'^```\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    try:
        return json.loads(text)
    except:
        # Try to find JSON object in text
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
        return {}

class JDInput(BaseModel):
    jd: str

class ResumeInput(BaseModel):
    jd: str
    resume: str

class PrepInput(BaseModel):
    jd: str

class MockInput(BaseModel):
    jd: str
    previous_qa: list = []
    user_answer: str = ""
    action: str = "start"
    total_questions: int = 5
    question_number: int = 1

@app.get("/")
def root():
    return {"status": "InterviewIQ API online", "version": "1.1"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/analyze-jd")
def analyze_jd(inp: JDInput):
    if not inp.jd.strip():
        raise HTTPException(status_code=400, detail="JD cannot be empty")
    prompt = f"""Analyze this job description and return a JSON object with exactly these keys:
- required_skills: array of 8-12 key technical/soft skills
- study_topics: array of 6-10 topics to study
- interview_questions: array of 8 objects, each with "question" and "category" (Technical|Behavioral|Situational)
- role_summary: string, 2-sentence summary

JD:
{inp.jd}

Return ONLY valid JSON."""
    result = parse_json(chat(prompt))
    if not result:
        result = {
            "required_skills": ["Python", "Problem Solving", "Communication", "Team Collaboration"],
            "study_topics": ["Data Structures", "System Design", "Algorithms", "OOP"],
            "interview_questions": [
                {"question": "Tell me about yourself.", "category": "Behavioral"},
                {"question": "What are your strengths?", "category": "Behavioral"},
                {"question": "Describe a challenging project.", "category": "Situational"}
            ],
            "role_summary": "This role requires strong technical and communication skills. Review the full JD for specific requirements."
        }
    return result

@app.post("/match-resume")
def match_resume(inp: ResumeInput):
    if not inp.jd.strip() or not inp.resume.strip():
        raise HTTPException(status_code=400, detail="JD and resume cannot be empty")
    prompt = f"""Compare this resume against the job description. Return a JSON object with exactly:
- match_score: integer 0-100
- summary: string, 1-2 sentence assessment
- matched_skills: array of matched skills (max 10)
- missing_skills: array of missing skills (max 8)
- gaps: array of objects with "area" and "description" (max 4)
- recommendations: array of 4-5 actionable strings

JD: {inp.jd}

RESUME: {inp.resume}

Return ONLY valid JSON."""
    result = parse_json(chat(prompt))
    if not result:
        result = {"match_score": 60, "summary": "Partial match detected. Review recommendations below.", "matched_skills": [], "missing_skills": [], "gaps": [], "recommendations": ["Tailor your resume to the JD", "Add missing keywords", "Highlight relevant projects"]}
    return result

@app.post("/interview-prep")
def interview_prep(inp: PrepInput):
    if not inp.jd.strip():
        raise HTTPException(status_code=400, detail="JD cannot be empty")
    prompt = f"""Create a comprehensive interview study plan. Return JSON with:
- study_schedule: string overview
- topics: array of 5-7 objects each with: name, priority (High/Medium/Low), study_time, description, concepts (array), resources (array of 3), questions (array of 3)

JD: {inp.jd}

Return ONLY valid JSON."""
    result = parse_json(chat(prompt))
    if not result:
        result = {"study_schedule": "Spend 1 week on core topics, focusing on high priority items first.", "topics": []}
    return result

@app.post("/mock-interview")
def mock_interview(inp: MockInput):
    if not inp.jd.strip():
        raise HTTPException(status_code=400, detail="JD cannot be empty")

    if inp.action == "start":
        prompt = f"""You are a professional technical interviewer. Generate the first interview question.
JD: {inp.jd}

Return JSON with: question (string), category (Technical|Behavioral|Situational)
Return ONLY valid JSON."""
        result = parse_json(chat(prompt))
        return result or {"question": "Tell me about yourself and your relevant experience.", "category": "Behavioral"}

    elif inp.action == "next":
        qa_history = "\n".join([f"Q: {qa.get('question','')}\nA: {qa.get('answer','')}" for qa in inp.previous_qa])
        prompt = f"""You are a professional technical interviewer. Evaluate the last answer and ask the next question.

JD: {inp.jd}
Conversation so far:
{qa_history}

Return JSON with:
- feedback: object with score (0-100), verdict (string), good_points (array 2-3), improve_points (array 2-3), ideal_hint (string)
- question: next question string
- category: Technical|Behavioral|Situational

Return ONLY valid JSON."""
        result = parse_json(chat(prompt))
        return result or {
            "feedback": {"score": 70, "verdict": "Good attempt", "good_points": ["Clear communication"], "improve_points": ["Add more specifics"], "ideal_hint": "Use the STAR method for behavioral questions."},
            "question": "Describe a challenging technical problem you solved.", "category": "Technical"
        }

    else:  # final
        qa_history = "\n".join([f"Q: {qa.get('question','')}\nA: {qa.get('answer','')}" for qa in inp.previous_qa])
        prompt = f"""You are a professional technical interviewer. Provide a final interview assessment.

JD: {inp.jd}
Full Interview:
{qa_history}

Return JSON with:
- feedback: object with score (0-100), verdict, good_points (array), improve_points (array), ideal_hint
- overall_score: integer 0-100
- strengths: array of 3-4 strings
- improvements: array of 3-4 strings

Return ONLY valid JSON."""
        result = parse_json(chat(prompt))
        return result or {
            "feedback": {"score": 70, "verdict": "Good overall performance", "good_points": ["Completed the interview"], "improve_points": ["Practice more"], "ideal_hint": ""},
            "overall_score": 70, "strengths": ["Communication", "Effort"], "improvements": ["Technical depth", "Specific examples"]
        }
