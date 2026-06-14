import time
from collections import defaultdict

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

WINDOW_SECONDS = 3600
MAX_AI_REQUESTS = 30

_buckets: dict[str, list[float]] = defaultdict(list)


class AIRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/ai/"):
            user_key = request.headers.get("authorization", "anonymous")[:64]
            now = time.time()
            window = [t for t in _buckets[user_key] if now - t < WINDOW_SECONDS]
            if len(window) >= MAX_AI_REQUESTS:
                raise HTTPException(status_code=429, detail="AI rate limit exceeded")
            window.append(now)
            _buckets[user_key] = window
        return await call_next(request)
