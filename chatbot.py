from fastapi import FastAPI
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import google.generativeai as genai
from fastapi.staticfiles import StaticFiles
import json
import time
from threading import Lock

class RateLimiter:
    def __init__(self, max_per_minute: int):
        self.max = max_per_minute
        self.calls = []
        self.lock = Lock()

    def allow(self) -> bool:
        now = time.time()
        with self.lock:
            # purge calls older than 60s
            self.calls = [t for t in self.calls if now - t < 60]
            if len(self.calls) < self.max:
                self.calls.append(now)
                return True
            return False

chat_rate_limiter = RateLimiter(max_per_minute=15)
app = FastAPI()
@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   
    allow_methods=["*"],
    allow_headers=["*"],
)
class ExtractionRequest(BaseModel):
    aim_text: str
    num_phrases: Optional[int] = 5
    num_questions_per_phrase: Optional[int] = 3

class ExtractionResponse(BaseModel):
    phrases: List[str]
    questions: List[str]
with open("aim.md", "r", encoding="utf-8") as f:
    AIM_CONTENT = f.read()
genai.configure(api_key="AIzaSyABEoJi0SpQrt7iVXKMnyklgnGWXx31sew")
class ChatMessage(BaseModel):
    role: str      
    content: str    

class ChatRequest(BaseModel):
    message: str
    has_used_before: bool
    conversation_history: Optional[List[ChatMessage]] = []
@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Empty message not allowed.")
    classification_instruction = (
        f"You are a highly knowledgeable and focused Virtual Lab AI lab assistant. Your sole purpose is to help users with science and engineering lab-related topics including "
        f"Lab experiments and procedures, Engineering theory relevant to labs, Instrumentation and equipment usage, Data analysis and scientific interpretation, Safety protocols and best practices, Field-related technical questions"
    f"You must not answer any question that is NOT DIRECTLY related to science, engineering, or lab work. If a question is outside this scope (e.g., general knowledge, entertainment, personal advice), respond with:\" I'm here to assist only with lab and engineering-related topics. Please ask a question related to science or laboratory work\""
    f"Always keep your responses factual, concise, and focused on the topic. Use technical language suitable for students or professionals in STEM fields, but explain clearly when concepts may be complex."
    )
    if req.has_used_before:
        prompt = (
            f"{classification_instruction}\n\n"
            "You are a highly knowledgeable and focused Virtual Lab AI lab assistant. Your sole purpose is to help new users with science and engineering lab-related topics including "
        f"Lab experiments and procedures, Engineering theory relevant to labs, Instrumentation and equipment usage, Data analysis and scientific interpretation, Safety protocols and best practices, Field-related technical questions"
        f"You must not answer any question that is NOT DIRECTLY related to science, engineering, or lab work. If a question is outside this scope (e.g., general knowledge, entertainment, personal advice), respond with:\" I'm here to assist only with lab and engineering-related topics. Please ask a question related to science or laboratory work\""
    f"Always keep your responses factual, concise, and focused on the topic. Use technical language suitable for students or professionals in STEM fields, but explain clearly when concepts may be complex."
            f"Answer clearly and simply:\n\n{req.message}"
        )
    else:
        prompt = (
            f"{classification_instruction}\n\n"
            "You are a highly knowledgeable and focused Virtual Lab AI lab assistant. Your sole purpose is to help users with science and engineering lab-related topics including "
        f"Lab experiments and procedures, Engineering theory relevant to labs, Instrumentation and equipment usage, Data analysis and scientific interpretation, Safety protocols and best practices, Field-related technical questions"
        f"You must not answer any question that is NOT DIRECTLY related to science, engineering, or lab work. If a question is outside this scope (e.g., general knowledge, entertainment, personal advice), respond with:\" I'm here to assist only with lab and engineering-related topics. Please ask a question related to science or laboratory work\""
    f"Always keep your responses factual, concise, and focused on the topic. Use technical language suitable for students or professionals in STEM fields, but explain clearly when concepts may be complex."
            f"Answer clearly and simply:\n\n{req.message}"
        )

    try:
        gemini_history = []
        for msg in req.conversation_history:
            role = "user" if msg.role == "user" else "model"
            gemini_history.append({
                "role": role,
                "parts": [
                    { "text": msg.content }
                ]
            })
        model = genai.GenerativeModel("gemini-2.0-flash")
        chat = model.start_chat(history=gemini_history)
        gemini_resp = chat.send_message(prompt)
        return { "response": gemini_resp.text }

    except Exception as e:
        # If the Gemini API fails for any reason, return an error string
        return { "response": f"Error from Gemini API: {str(e)}" }
    
    
@app.post("/extract_and_questions", response_model=ExtractionResponse)
async def extract_and_questions(req: ExtractionRequest):
    """
    1. Ask Gemini to pull out the top N scientific phrases.
    2. Ask Gemini to generate M simple questions per phrase.
    """
    # 1) Extraction prompt
    extract_prompt = f"""
Extract the {req.num_phrases} most important domain-specific phrases (1–4 words each) from the following experimental aim.
Return them as a JSON array of strings, no extra text.

Aim:
\"\"\"{req.aim_text}\"\"\"
"""
    model = genai.GenerativeModel("gemini-2.0-flash")
    extraction_chat = model.start_chat()
    extraction_resp = extraction_chat.send_message(extract_prompt).text

    # parse the JSON array (simple eval; in production use json.loads)
    try:
        phrases = json.loads(extraction_resp)
    except:
        # fallback: split on newlines
        phrases = [line.strip("- ").strip() 
                   for line in extraction_resp.splitlines() if line.strip()]

    # 2) Question-generation prompt
    # Build a prompt that feeds back those phrases
    qgen_prompt = f"""
I have these key phrases from an experiment:

{json.dumps(phrases, indent=2)}

For each phrase, write {req.num_questions_per_phrase} simple, one-sentence questions a student might ask to check understanding.
Return as a flat JSON array of strings.
"""
    qgen_chat = model.start_chat()
    qgen_resp = qgen_chat.send_message(qgen_prompt).text

    try:
        questions = json.loads(qgen_resp)
    except:
        questions = [line.strip("- ").strip() 
                     for line in qgen_resp.splitlines() if line.strip()]

    return {"phrases": phrases, "questions": questions}
