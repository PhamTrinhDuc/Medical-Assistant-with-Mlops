from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    # ⚠️ Truncate to 72 bytes (not characters!)
    password_bytes = password.encode("utf-8")
    truncated_bytes = password_bytes[:72]
    truncated_password = truncated_bytes.decode("utf-8", errors="ignore")
    return pwd_context.hash(truncated_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    return pwd_context.verify(plain_password, hashed_password)