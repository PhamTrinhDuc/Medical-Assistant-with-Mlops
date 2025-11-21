import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from utils.email_sender import send_email
from chains.paper_trend_chain import PaperSearcher, PaperTrendChain

DEFAULT_CATEGORIES = {
    "llm": ["cs.CL", "cs.LG", "stat.ML"],
    "vision": ["cs.CV"],
    "robotics": ["cs.RO"],
    "general": ["cs.AI", "cs.LG", "stat.ML"]
}

routes = APIRouter()

@routes.get("/paper-trend", response_class=JSONResponse)
async def send_paper_trend_email(
  to_email: str = Query(..., description="Recipient's email address"),
  topic: str = Query(..., description="Topic requested by the user"),
  days: int = Query(..., description="Number of days to search for papers"),
  top_k: int = Query(..., description="Number of top papers to return"),
):
  """
  Endpoint to send an email containing paper trends.

  Args:
    to_email (str): Recipient's email address.
    topic (str): Topic requested by the user.
    days (int): Number of days to search for papers.
    top_k (int): Number of top papers to return.

  Returns:
    JSONResponse: Confirmation of email sent.
  """
  try:
    searcher = PaperSearcher()

    papers = searcher.search_relevent_papers(query=topic, 
                                            days=days, 
                                            top_k=top_k,
                                            max_results=10, 
                                            categories=DEFAULT_CATEGORIES[topic])

    chain = PaperTrendChain()
    degist_html = chain.generate_digest_html(topic=topic, papers=papers)

    send_email(
      to_emails=to_email, 
      subject=topic, 
      html_body=degist_html
    )
    return JSONResponse(content={"message": "Email sent successfully."}, status_code=200)
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
  

