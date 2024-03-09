from starlette.middleware.base import BaseHTTPMiddleware

import logging
import time

logger = logging.root
handler = logging.StreamHandler()

logger.handlers = [handler]
logger.setLevel(logging.DEBUG)

logging.getLogger("uvicorn.access").disabled = True

class LogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        timer = time.time()
        response = await call_next(request)
        timer = (time.time() - timer) * 1000
        logger.info(f"{request.method} {request.url.path} {timer:.0f}ms\n  Query: {request.url.query}\n  User: {request.client.host} Agent: {request.headers.get('user-agent')}")
        return response