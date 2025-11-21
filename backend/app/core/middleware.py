import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from utils.logger import trace_id_ctx

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

class TraceIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Tạo trace_id duy nhất cho mỗi request
        trace_id = str(uuid.uuid4())
        
        # Set context với token để đảm bảo context được truyền đúng
        token = trace_id_ctx.set(trace_id)
        
        try:
            response = await call_next(request)
            response.headers['X-Trace-ID'] = trace_id
            return response
        finally:
            # Reset context sau khi xử lý xong
            trace_id_ctx.reset(token)

def setup_middlewares(app):
    # Thêm TraceIDMiddleware để gán trace_id cho mỗi request
    app.add_middleware(TraceIDMiddleware)
    
    # Cấu hình CORS Middleware nếu cần thiết
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[FRONTEND_URL], 
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )