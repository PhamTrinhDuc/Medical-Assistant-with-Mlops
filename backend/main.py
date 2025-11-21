from agents.hospital_rag_agent import HospitalRAGAgent
from utils.helper import async_retry

from fastapi import FastAPI

app = FastAPI(
    title="Hospital Chatbot",
    description="Endpoints for a hospital system graph RAG chatbot",
)


@app.get("/health")
async def get_status():
    return {"status": "running"}

# script: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
