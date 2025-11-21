
import os
import sys
import time
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from entities.conversation import Conversation, Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload
from utils.llm_wrapper import ProviderWrapper
from langchain.output_parsers import StructuredOutputParser

#### LƯU Ý: 
# conversation_id: đây là khóa ngoại của bảng messages liên kết đến khóa chính của bảng conversations (kiểu int). 
# session_id: là chuỗi định danh phiên của conversation đó (kiểu str).

class ConversationService:
  def __init__(self, db_session: AsyncSession):
    self.db_session = db_session

  async def create_conversation(self, user_id: int)-> str:
    """Tạo một conversation mới cho user và trả về session_id"""
    session_id = f"{user_id}_{int(time.time())}"
    conversation = Conversation(
      user_id=user_id, 
      session_id=session_id,
      title="New Conversation", 
    )
  
    self.db_session.add(conversation)
    await self.db_session.commit()
    await self.db_session.refresh(conversation)
    return conversation.session_id

  async def get_conversations(self, user_id: int) -> list[Conversation]:
    """Lấy tất cả titles conversation của user dựa vào user_id, chỉ lấy title và session_id"""
    stmt = (
      select(Conversation)
      .where(Conversation.user_id == user_id)
      .options(selectinload(Conversation.messages))
      .order_by(Conversation.updated_at.desc())
    )
    
    result = await self.db_session.execute(stmt)
    title_conversations = result.scalars().all()
    return list(title_conversations)

  async def get_conversation_by_session_id(self, user_id: int, session_id: str) -> Conversation | None:
    """Lấy một conversation dựa vào id của conversation và user_id"""
    stmt = (
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .where(Conversation.session_id == session_id)
        .options(selectinload(Conversation.messages))
    )
    
    result = await self.db_session.execute(stmt)
    conversation = result.scalar_one_or_none()
    return conversation
  
  async def get_messages(self, user_id: str, session_id: str) -> list[Message]:
    """Lấy tất cả messages của một conversation dựa vào id của phiên trò chuyện"""
    stmt = (
        select(Message)
        .join(Conversation)
        .where(Conversation.user_id == user_id)
        .where(Conversation.session_id == session_id)
        .order_by(Message.created_at)
    )
    
    result = await self.db_session.execute(stmt)
    messages = result.scalars().all()
    return list(messages)
    
  async def save_message(self, 
                         user_id: int,
                         session_id: str, 
                         message_type: str,
                         content: str) -> int:
    """Lưu một message vào conversation dựa vào session_id"""

    stmt = select(Conversation.id).where(Conversation.session_id==session_id, Conversation.user_id==user_id)
    result = await self.db_session.execute(stmt)
    conversation_id = result.scalar_one_or_none()

    message = Message(
      conversation_id=conversation_id, 
      message_type=message_type, 
      content=content
      )

    self.db_session.add(message)
    await self.db_session.commit()
    await self.db_session.refresh(message)
    return message.id

  async def delete_conversation(self, user_id: int, session_id: str):
    """Xóa một conversation và tất cả messages liên quan dựa vào session_id"""
    stmt = delete(Conversation).where(Conversation.user_id==user_id, Conversation.session_id==session_id)
    result = await self.db_session.execute(stmt)
    await self.db_session.commit()
    
    return result.rowcount > 0  # Trả về True nếu đã xóa
  
  def _generate_title(self, user_query: str) -> str:
    """Tạo title cho conversation dựa vào user_query"""
    llm = ProviderWrapper.get_model("google")
    response = llm.invoke(input=f"tạo tiêu đề của cuộc trò chuyện dựa vào câu hỏi đầu tiên của user: {user_query}.Giới hạn khoảng 5 từ và không thêm gì khác.")
    return response.content.strip()

  async def update_title_conversation(self, user_id: int, session_id: str, user_query: str):
    """Cập nhật title của conversation dựa vào session_id"""
    new_title = self._generate_title(user_query)
    
    stmt = (
      update(Conversation)
      .where(Conversation.user_id==user_id, Conversation.session_id==session_id)
      .values(title=new_title, updated_at=datetime.utcnow())
    )
    await self.db_session.execute(stmt)
    await self.db_session.commit()
   