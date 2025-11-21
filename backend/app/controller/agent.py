import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import (
  Request, 
  APIRouter, 
  HTTPException, 
  Path, Body, Depends
)
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse, StreamingResponse
from agent.agent_research import AgentResearch
from services.conversation import ConversationService
from models import AgentRequest, AgentResponse
from core.auth_middleware import get_current_user
from utils.database import get_db
from utils.logger import logger

routes = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@routes.post("/chat/session/{session_id}", response_model=AgentResponse)
@limiter.limit("10/minute")
async def agent_chat(
  request: Request, # limiter cần lấy thông tin để rate-limit: IP, headers, user-agent v.v. Tất cả nằm trong Request object.
  session_id: str = Path(..., description="session chat"), 
  payload: AgentRequest = Body(...), 
  current_user = Depends(get_current_user), 
  db: AsyncSession = Depends(get_db)
):
  
  logger.info(f"Chat request - POST - /chat/session - User: {current_user.id} - Session: {session_id}")

  # Validate role 
  conv_service = ConversationService(db) 
  conversation = await conv_service.get_conversation_by_session_id(user_id=current_user.id, 
                                                                   session_id=session_id)
  if not conversation: 
     logger.warning(f"Unauthorized access attempt to session {session_id} by user {current_user.id}")
     raise HTTPException(status_code=403, detail="You do not have access to this session.")
  
  try:
    # save message from user 
    await conv_service.save_message(
      user_id=current_user.id,
      session_id=session_id,
      message_type="user", 
      content=payload.query
    )

    # Get agent response before committing anything
    agent = AgentResearch(session_id=session_id, model=payload.model)
    response = await agent.ainvoke(query=payload.query)

    # Save assistant response
    await conv_service.save_message(
      user_id=current_user.id,
      session_id=session_id,
      message_type="assistant", 
      content=response.get("output").strip()
    )

    # Only commit if everything succeeds
    await db.commit()
    
    return AgentResponse(
      success=True,
      status_code=200,
      message="Agent response generated successfully",
      output=response.get("output").strip(),
      intermediate_steps=response.get("intermediate_steps", [])
    )
        
  except Exception as e:
    await db.rollback()
    logger.error(f"Failed to get response from agent: {str(e)}")
    raise HTTPException(status_code=500, detail=f"Failed to get response from agent. Server internal error")
  

@routes.post("/stream/session/{session_id}")
@limiter.limit("10/minute")
async def agent_stream(
  request: Request,
  session_id: str = Path(..., description="session chat"), 
  payload: AgentRequest = Body(...), 
  current_user = Depends(get_current_user), 
  db: AsyncSession = Depends(get_db),
): 
  
  logger.info(f"Agent streaming response - POST - /stream/session. User id{current_user.id} - Session id: {session_id}")

  # Validate role 
  conv_service = ConversationService(db) 
  conversation = await conv_service.get_conversation_by_session_id(user_id=current_user.id, 
                                                                   session_id=session_id)
  if not conversation: 
     logger.warning(f"Unauthorized access attempt to session {session_id} by user {current_user.id}")
     raise HTTPException(status_code=403, detail="You do not have access to this session.")
  
  try: 
    # Save user message first
    await conv_service.save_message(
      user_id=current_user.id,
      session_id=session_id,
      message_type="user", 
      content=payload.query
    )
    
    # Commit user message first for streaming (since we need to stream immediately)
    await db.commit()

    agent = AgentResearch(session_id=session_id, model=payload.model)

    import json
    
    async def stream_response(): 
      try: 
        full_output = ""
        all_intermediate_steps = []
        
        async for chunk in agent.astream(query=payload.query):
          # Parse intermediate steps if present
          if 'steps' in chunk:
            for step in chunk.get('steps', []):
              # Handle both tuple format and AgentStep object format
              if isinstance(step, (list, tuple)):
                action = step[0]
                observation = step[1]
              else:
                # step is an AgentStep object
                action = step
                observation = getattr(step, 'observation', '')
              
              tool_name = getattr(action, 'tool', str(action))
              tool_input = getattr(action, 'tool_input', {})
              
              step_data = {
                "tool": tool_name,
                "input": tool_input if isinstance(tool_input, dict) else str(tool_input),
                "observation": str(observation)
              }
              all_intermediate_steps.append(step_data)
              
              # Yield intermediate step
              yield json.dumps({
                "type": "step",
                "data": step_data
              }) + "\n"
          
          # Handle agent output
          if 'output' in chunk:
            full_output = chunk['output']
            # Yield final output
            yield json.dumps({
              "type": "output",
              "output": full_output,
              "intermediate_steps": all_intermediate_steps
            }) + "\n"
        
        # Save assistant response to database
        if full_output:
          from utils.database import AsyncSessionLocal
          async with AsyncSessionLocal() as new_session:
            conv_service_new = ConversationService(new_session)
            await conv_service_new.save_message(
              user_id=current_user.id,
              session_id=session_id,
              message_type="assistant", 
              content=full_output
            )
            await new_session.commit()
            
      except Exception as e: 
        logger.error(f"Error during streaming response: {str(e)}")
        yield json.dumps({
          "type": "error",
          "error": str(e)
        }) + "\n"
        
    return StreamingResponse(stream_response(), media_type="application/x-ndjson", status_code=200)

  except Exception as e: 
    # Rollback if error happens before streaming starts
    await db.rollback()
    logger.error(f"Error during process request streaming: {str(e)}")
    raise HTTPException(status_code=500, detail="Failed to process request. Server internal error")
  

