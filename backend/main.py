from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import json, re, os

app = FastAPI(title="InterviewIQ API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Supports Groq (free), OpenAI, or any OpenAI-compatible endpoint
API_BASE = os.environ.get("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")
API_KEY  = os.environ.get("OPENAI_API_KEY", "")
MODEL    = os.environ.get("AI_MODEL", "llama-3.3-70b-versatile")

client = OpenAI(base_url=API_BASE, api_key=API_KEY)

def chat(prompt: str, system: str = "You are an expert AI career coach and technical interviewer.") -> str:
    res = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        max_tokens=2048
    )
    return res.choices[0].message.content

def parse_json(text: str) -> dict:
    text = re.sub(r'^```json\s*', '', text.strip())
    text = re.sub(r'^```\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    try:
        return json.loads(text)
    except:
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

@app.post("/analyze-jd")
def analyze_jd(inp: JDInput):
    prompt = f"""Analyze this job description and return a JSON object with:
- required_skills: list of 8-12 key technical/soft skills required
- study_topics: list of 6-10 topics the candidate should study
- interview_questions: list of 8 likely interview questions, each as {{"question": "...", "category": "Technical|Behavioral|Situational"}}
- role_summary: 2-sentence summary of the role

JD:
{inp.jd}

Return ONLY valid JSON, no other text."""
    result = parse_json(chat(prompt))
    if not result:
        result = {"required_skills":["Python","FastAPI","SQL"],"study_topics":["Data Structures","System Design"],"interview_questions":[{"question":"Tell me about yourself.","category":"Behavioral"}],"role_summary":"Technical role requiring strong engineering skills."}
    return result

@app.post("/match-resume")
def match_resume(inp: ResumeInput):
    prompt = f"""Compare this resume against the job description and return a JSON object with:
- match_score: integer 0-100 indicating how well resume matches JD
- summary: 1-2 sentence overall assessment
- matched_skills: list of skills present in both JD and resume (max 10)
- missing_skills: list of skills required in JD but not in resume (max 8)
- gaps: list of gap objects {{"area": "...", "description": "..."}} (max 4)
- recommendations: list of 4-5 actionable recommendations to improve the match

JD:
{inp.jd}

RESUME:
{inp.resume}

Return ONLY valid JSON."""
    result = parse_json(chat(prompt))
    if not result:
        result = {"match_score":60,"summary":"Partial match detected.","matched_skills":[],"missing_skills":[],"gaps":[],"recommendations":["Review JD requirements carefully."]}
    return result

@app.post("/interview-prep")
def interview_prep(inp: PrepInput):
    prompt = f"""Create a comprehensive interview study plan for this job description. Return JSON with:
- study_schedule: overall study plan as a string (e.g. "Spend 3 days on core topics...")
- topics: list of 5-7 topic objects, each with:
  - name: topic name
  - priority: "High"|"Medium"|"Low"
  - study_time: estimated study time (e.g. "3-4 hours")
  - description: 1-2 sentence description
  - concepts: list of 4-6 key concepts to learn
  - resources: list of 3 specific resources/links to study
  - questions: list of 3 practice questions for this topic

JD:
{inp.jd}

Return ONLY valid JSON."""
    result = parse_json(chat(prompt))
    if not result:
        result = {"study_schedule":"Focus on core topics first.","topics":[]}
    return result

@app.post("/mock-interview")
def mock_interview(inp: MockInput):
    if inp.action == "start":
        prompt = f"""You are a technical interviewer. Generate the FIRST interview question for this role.
JD: {inp.jd}

Return JSON with:
- question: the interview question (make it relevant, specific, not too easy)
- category: "Technical"|"Behavioral"|"Situational"

Return ONLY valid JSON."""
        result = parse_json(chat(prompt))
        return result or {"question":"Tell me about yourself and your relevant experience.","category":"Behavioral"}

    elif inp.action == "next":
        qa_history = "\n".join([f"Q: {qa['question']}\nA: {qa['answer']}" for qa in inp.previous_qa])
        prompt = f"""You are a technical interviewer. Generate feedback on the last answer AND the next question.

JD: {inp.jd}
Previous Q&A:
{qa_history}

Return JSON with:
- feedback: object with score (0-100), verdict, good_points (list 2-3), improve_points (list 2-3), ideal_hint
- question: next interview question
- category: "Technical"|"Behavioral"|"Situational"

Return ONLY valid JSON."""
        result = parse_json(chat(prompt))
        return result or {"feedback":{"score":70,"verdict":"Good attempt","good_points":["Relevant answer"],"improve_points":["Be more specific"],"ideal_hint":"Use STAR method."},"question":"Describe a challenging project.","category":"Behavioral"}

    else:
        qa_history = "\n".join([f"Q: {qa['question']}\nA: {qa['answer']}" for qa in inp.previous_qa])
        prompt = f"""You are a technical interviewer. Provide final assessment.

JD: {inp.jd}
Full Q&A:
{qa_history}

Return JSON with:
- feedback: object with score, verdict, good_points, improve_points, ideal_hint
- overall_score: integer 0-100
- strengths: list of 3-4 overall strengths
- improvements: list of 3-4 key areas to improve

Return ONLY valid JSON."""
        result = parse_json(chat(prompt))
        return result or {"feedback":{"score":70,"verdict":"Good performance","good_points":["Answered questions"],"improve_points":["Practice more"],"ideal_hint":""},"overall_score":70,"strengths":["Communication"],"improvements":["Technical depth"]}

@app.get("/")
def root():
    return {"status": "InterviewIQ API online", "version": "1.0"}
