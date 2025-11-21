import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", '..'))
from pydantic import BaseModel, Field, validator
from enum import StrEnum
from app_config import AppConfig

class ModelEnum(StrEnum):
  OPENAI = "openai"
  GOOGLE = "google"

class AgentRequest(BaseModel):
  query: str = Field(..., min_length=1, max_length=4000, description="User's query")
  model: ModelEnum = Field(default=ModelEnum.GOOGLE, description="Model to use for the agent")

  @validator('query')
  def validate_query(cls, v):
    if not v.strip():
      raise ValueError('Query must not be empty or whitespace')
    return v.strip()


# class RoleEnum(StrEnum):
#   USER = "user"
#   AGENT = "assistant"

# class ChatMessageResponse(BaseModel):
#   role: RoleEnum = Field(..., description="Role of the message sender")
#   content: str = Field(..., description="Content of the message")
#   model: ModelEnum = Field(..., description="Model used to generate the message")
#   timestamp: str = Field(..., description="Timestamp of the message creation")

class AgentResponse(BaseModel):
  success: bool = Field(..., description="Indicates if the agent successfully processed the request")
  status_code: int = Field(..., description="HTTP status code of the response")
  message: str = Field(..., description="A message providing additional information about the response")
  output: str = Field(..., description="Response from the agent")
  intermediate_steps: list = Field(default=[], description="Intermediate steps taken by the agent. Each step contains tool name, input, and observation")