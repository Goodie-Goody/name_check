'''
Security Headers Middleware.

This middleware adds essential security headers to HTTP responses to protect
against common web vulnerabilities like XSS, clickjacking, and MIME type sniffing.
'''

from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    '''
    Middleware to apply security headers.

    This class sets headers that help secure web applications by implementing
    policies against cross-site scripting, frame loading from different origins,
    and more.
    '''
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net blob:; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; " #pylint: disable=line-too-long
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' https://fastapi.tiangolo.com; "
            "worker-src 'self' blob:"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
