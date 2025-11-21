import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from sqlalchemy.ext.asyncio import AsyncSession
from entities.users import User
from sqlalchemy import select
from utils.security import hash_password, verify_password
from utils.logger import logger


class UserService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_user(self, 
                    full_name: str,
                    username: str, 
                    password: str, 
                    validate_password: str,
                    email: str=None) -> User:
      
      """Tạo một user mới và trả về đối tượng User"""

      if password != validate_password:
        raise ValueError("Password và Validate Password không khớp")
    
      hashed_password = hash_password(password)

      new_user = User(username=username, 
                      full_name=full_name, 
                      password=hashed_password,
                      email=email)
      
      self.db_session.add(new_user)
      await self.db_session.commit()
      await self.db_session.refresh(new_user)
      return new_user
    
    async def get_user_by_id(self, user_id: int) -> User | None:
      result = await self.db_session.get(User, user_id)
      return result 
    

    async def get_all_users(self) -> list[User]:
      stmt = select(User)
      result = await self.db_session.execute(stmt)
      users = result.scalars().all()
      return users
    

    async def get_user_by_username(self, identifier: str) -> User | None:
      """Lấy user theo username hoặc email"""
      stmt = select(User).where((User.username == identifier) | (User.email == identifier))
      result = await self.db_session.execute(stmt)
      return result.scalar_one_or_none()
    
    async def verify_credentials(self, 
                                 password: str,
                                 identifier: str) -> User | None:
      
      """Verify username và password (dùng cho login)"""
      user = await self.get_user_by_username(identifier)
      
      if not user:
        logger.warning(f"Không tìm thấy user với Identifier: {identifier}")
        raise ValueError("User không tồn tại")
      if not verify_password(password, user.password):
        logger.warning(f"Password không đúng cho user: {identifier}")
        return None
      
      return user