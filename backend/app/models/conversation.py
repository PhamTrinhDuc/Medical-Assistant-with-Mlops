from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional, Any

class MessageSchema(BaseModel):
    id: int
    content: str
    message_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)  # ← thay vì orm_mode=True (Pydantic v2)

class ConversationSchema(BaseModel):
    id: int
    user_id: int
    session_id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: Optional[List[MessageSchema]] = None  # nếu cần

    model_config = ConfigDict(from_attributes=True)

class ConversationResponse(BaseModel):
    status_code: int = 200
    success: bool = False
    message: str = ""
    content: Any = None

    model_config = ConfigDict(from_attributes=True)