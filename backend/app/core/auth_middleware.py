import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Optional
from fastapi.security import HTTPBearer

from utils.database import get_db
from services.user import UserService
from entities.users import User
from app_config import AppConfig
from utils.logger import logger

security = HTTPBearer()

async def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Tạo JWT access token.
    
    Args:
        data: Dữ liệu cần encode trong token
        expires_delta: Thời gian hết hạn (tùy chọn)
        
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=AppConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, AppConfig.SECRET_KEY, algorithm=AppConfig.ALGORITHM)
    
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), 
                           db: AsyncSession = Depends(get_db)) -> User:
    """
    Xác thực và lấy thông tin người dùng hiện tại từ token.
    Args:
        credentials: HTTPAuthorizationCredentials từ Bearer token
        db: Database session
    Returns:
        Đối tượng User đã xác thực
    Raises:
        HTTPException: Nếu token không hợp lệ hoặc người dùng không tồn tại
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực thông tin đăng nhập",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=401, 
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    token = credentials.credentials
    
    try:
        # Giải mã token
        payload = jwt.decode(token, AppConfig.SECRET_KEY, algorithms=[AppConfig.ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
        
    except JWTError as e:
        raise credentials_exception
    
    user_service = UserService(db_session=db)
    # Lấy thông tin người dùng từ database
    user = await user_service.get_user_by_id(user_id=int(user_id))
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị vô hiệu hóa",
        )
    
    return user


# async def get_current_active_superuser(current_user: User = Depends(get_current_user)) -> User:
#     """
#     Kiểm tra xem người dùng hiện tại có phải là superuser hay không.
    
#     Args:
#         current_user: Người dùng hiện tại
        
#     Returns:
#         Đối tượng User nếu là superuser
        
#     Raises:
#         HTTPException: Nếu người dùng không phải superuser
#     """
#     if not current_user.is_superuser:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Bạn không có quyền truy cập chức năng này",
#         )
    
#     return current_user
