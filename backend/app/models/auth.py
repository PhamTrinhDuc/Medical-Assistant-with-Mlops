
from pydantic import BaseModel, Field, ConfigDict

class RegisterRequest(BaseModel):
  full_name: str
  username: str=None
  validate_password: str = Field(..., min_length=8)
  password: str = Field(..., min_length=8)
  email: str=None

  model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
  identifier: str
  password: str

  model_config = ConfigDict(from_attributes=True)

class AuthResponse(BaseModel):
  status_code: int = 200
  success: bool = False
  message: str = ""
  content: dict = {}

  model_config = ConfigDict(from_attributes=True)
