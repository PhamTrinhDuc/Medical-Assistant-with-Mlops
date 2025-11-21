import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from fastapi import Depends, Query, APIRouter, Path
from utils.database import get_db
from utils.logger import logger
from services.conversation import ConversationService
from core.auth_middleware import get_current_user
from models.conversation import MessageSchema, ConversationSchema, ConversationResponse

routes = APIRouter()


@routes.post("/conversations", response_model=ConversationResponse)
async def new_conversation(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"Creating new conversation. user_id: {current_user.id}")

    try:
        service = ConversationService(db_session=db)
        session_id = await service.create_conversation(user_id=current_user.id)

        return ConversationResponse(
            status_code=200,
            success=True,
            message="Conversation created successfully",
            content={"session_id": str(session_id)}
        )
    
    except SQLAlchemyError as e:
      logger.error(f"Database error. user_id: {current_user.id}")
      raise HTTPException(status_code=500, detail="Database error occurred")
    
    except Exception as e:
      logger.exception(f"Unexpected error. user_id: {current_user.id}")
      raise HTTPException(status_code=500, detail="Create conversation failed")


@routes.get("/conversations", response_model=ConversationResponse)
async def get_conversations(
  current_user=Depends(get_current_user),
  db: AsyncSession = Depends(get_db), 
  limit: int = Query(10, description="Num of conversations", ge=1, le=100), 
  offset: int = Query(0, description="Offset for pagination", ge=0)):

  logger.info(f"Get conversations. /get_conversations - GET. User ID: {current_user.id}")

  try: 
      service = ConversationService(db_session=db)
      conversations = await service.get_conversations(user_id=current_user.id)
      response =  [ConversationSchema.model_validate(conv) for conv in conversations]
      return ConversationResponse(
          content=response,
          success=True,
          status_code=200,
          message="Get conversations successfully"
      )
  except SQLAlchemyError as e:
    logger.error(f"Database error while getting conversations. {str(e)}")
    raise HTTPException(status_code=500, detail="Database error occurred")
  
  except Exception as e:
      logger.exception(f"Error getting conversations. {str(e)}")
      raise HTTPException(status_code=500, detail="Get conversations failed")


@routes.delete("/conversation/{session_id}", response_model=ConversationResponse)
async def delete_conversation(
    session_id: Annotated[str, Path(..., description="ID của conversation")], 
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    
    logger.info(f"Delete conversation. /delete_conversation - DELETE. User ID: {current_user.id}, Conversation ID: {session_id}")

    try: 
        service = ConversationService(db_session=db)
        is_deleted =  await service.delete_conversation(user_id=current_user.id, 
                                                        session_id=session_id)
        
        if is_deleted:
            return ConversationResponse(
                content={"deleted": True},
                success=True,
                status_code=200,
                message="Delete conversation successfully"
            )
        else:
            return ConversationResponse(
                content={"deleted": False},
                success=False,
                status_code=404,
                message="Conversation not found"
            )
        
    except Exception as e:
      logger.error(f"Error deleting conversation. Error: {str(e)}")
      return HTTPException(status_code=500, detail="Delete conversation failed")
    

@routes.get("/conversations/{session_id}/messages", response_model=ConversationResponse)
async def get_messages(
    session_id: Annotated[str, Path(..., description="ID of conversation")], 
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):

    logger.info(f"Get messages. /get_messages - GET. User ID: {current_user.id}, Conversation ID: {session_id}")

    try: 
      service = ConversationService(db_session=db)
      messages = await service.get_messages(user_id=current_user.id, 
                                          session_id=session_id)
      response = [MessageSchema.model_validate(msg) for msg in messages]
      return ConversationResponse(
          content=response,
          success=True,
          status_code=200,
          message="Get messages successfully"
      )
    
    except Exception as e:
      logger.error(f"Error getting messages. Error: {str(e)}")
      raise HTTPException(status_code=500, detail="Get messages failed")


@routes.post("/conversations/{session_id}/title", response_model=ConversationResponse)
async def update_title_conversation(
  session_id: Annotated[str, Path(..., description="ID of conversation")], 
  current_user=Depends(get_current_user),
  db: AsyncSession = Depends(get_db)):

  logger.info(f"Update conversation title. /update_title_conversation - POST. User ID: {current_user.id}, Conversation ID: {session_id}")

  try: 
    service = ConversationService(db_session=db)
    conversation = await service.get_conversation_by_session_id(user_id=current_user.id, 
                                                              session_id=session_id)
    if not conversation:
        return ConversationResponse(
            success=False,
            status_code=404,
            message="Conversation not found"
        )
    
    await service.update_title_conversation(user_id=current_user.id, 
                                            session_id=session_id, 
                                            user_query=conversation.messages[0].content)
    
    return ConversationResponse(
        success=True,
        status_code=200,
        message="Update conversation title successfully"
    )
  
  except Exception as e:
    logger.error(f"Error updating conversation title. Error: {str(e)}")
    raise HTTPException(status_code=500, detail="Update conversation title failed")