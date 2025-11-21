
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from datetime import timedelta
from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from utils.database import get_db
from services.user import UserService
from models.auth import (
  RegisterRequest, 
  LoginRequest, 
  AuthResponse
)
from utils.logger import logger
from core.auth_middleware import get_current_user, create_access_token
from app_config import AppConfig

routes = APIRouter()


@routes.post("/register", response_model=AuthResponse)
async def register(
  request: RegisterRequest,
  db: AsyncSession = Depends(get_db)):

  logger.info(f"Register user: /register - POST. Username: {request.username}, Email: {request.email}")

  try:
    userService = UserService(db_session=db)
    user = await userService.create_user(
        full_name=request.full_name,
        username=request.username,
        password=request.password,
        validate_password=request.validate_password,
        email=request.email
    )

    return AuthResponse(
      status_code=200,
      success=True,
      message="Regiter successfully",
      content={
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
      }
    )
  except Exception as e:
    logger.error(f"Error during registration. Error: {str(e)}")
    raise HTTPException(status_code=500, detail="Registration failed due to server error")


@routes.post("/login", response_model=AuthResponse)
async def login(
  request: LoginRequest, 
  db: AsyncSession = Depends(get_db)
):  
  logger.info(f"User login: /login - POST. Identifier: {request.identifier}")
  try: 
    userService = UserService(db_session=db)
    user = await userService.verify_credentials(
        identifier=request.identifier,
        password=request.password
    )

    if not user:
      logger.warning(f"Login failed for Identifier: {request.identifier}")
      raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token_expires = timedelta(minutes=AppConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return AuthResponse(
      status_code=200,
      success=True,
      message="Register successfully",
      content={
        "token": access_token,
        "user": {
          "id": user.id,
          "username": user.username,
          "email": user.email,
          "fullName": user.full_name,
        }
      }
    )
  except Exception as e:
    logger.error(f"Error during login. Error: {str(e)}")
    raise HTTPException(status_code=500, detail="Login failed due to server error")


@routes.get("/me", response_model=AuthResponse)
async def get_current_user_info(
    current_user = Depends(get_current_user)
):
    """
    Get current authenticated user's information.
    """
    return AuthResponse(
      status_code=200,
      success=True,
      message="Get current user info successfully",
      content={
          "user": {
              "id": current_user.id,
              "username": current_user.username,
              "email": current_user.email,
              "fullName": current_user.full_name,
              "isActivate": current_user.is_active,
              "createdAt": current_user.created_at,
              "updatedAt": current_user.updated_at,
          }
      }
  )


@routes.get("/users", response_model=AuthResponse)
async def get_all_users(
    db: AsyncSession = Depends(get_db)
):
    """
    Get all registered users.
    """
    try:
      userService = UserService(db_session=db)
      users = await userService.get_all_users()

      users_data = [
        {
            "id": user.id,
            "username": user.username,
            "fullName": user.full_name,
            "isActivate": user.is_active,
        }
        for user in users
      ]

      return AuthResponse(
          status_code=200,
          success=True,
          message="Get all users successfully",
          content={"users": users_data}
      )
    except Exception as e:
      logger.error(f"Error fetching all users. Error: {str(e)}")
      raise HTTPException(status_code=500, detail="Error fetching users")