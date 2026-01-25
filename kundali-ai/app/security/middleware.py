"""
Security Middleware for Request Validation

Provides request-level security checks including:
- SQL injection detection in request bodies
- Input sanitization
- Rate limiting hooks
"""

import json
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.security.validators import detect_sql_injection


class SQLInjectionProtectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to detect and block SQL injection attempts.
    
    Scans JSON request bodies for potential SQL injection patterns.
    """
    
    # Paths to skip (static files, health checks, AI-generated content endpoints, etc.)
    SKIP_PATHS = ["/", "/health", "/docs", "/openapi.json", "/redoc"]
    
    # Path prefixes to skip (endpoints that may contain AI-generated text)
    SKIP_PREFIXES = [
        "/api/v1/pdf",           # PDF generation (AI predictions)
        "/api/v1/report",        # Report endpoints
        "/api/v1/kundali/report", # Kundali reports
        "/api/v1/ask",           # AI chat responses
        "/static",               # Static files
    ]
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Skip exact paths
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)
        
        # Skip prefixes (AI content endpoints)
        for prefix in self.SKIP_PREFIXES:
            if request.url.path.startswith(prefix):
                return await call_next(request)
        
        # Only check POST/PUT/PATCH requests with JSON body
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            
            if "application/json" in content_type:
                try:
                    # Read body
                    body = await request.body()
                    
                    if body:
                        try:
                            data = json.loads(body)
                            
                            # Recursively check for SQL injection
                            if self._scan_for_injection(data):
                                return JSONResponse(
                                    status_code=400,
                                    content={
                                        "detail": "Potentially malicious input detected. Request blocked."
                                    }
                                )
                        except json.JSONDecodeError:
                            pass  # Not JSON, continue
                        
                except Exception:
                    pass  # Error reading body, continue
        
        return await call_next(request)
    
    def _scan_for_injection(self, data, depth: int = 0) -> bool:
        """
        Recursively scan data structure for SQL injection patterns.
        
        Args:
            data: The data to scan (dict, list, or primitive)
            depth: Current recursion depth (to prevent DoS via deep nesting)
        
        Returns:
            True if injection detected, False otherwise
        """
        # Prevent excessive recursion
        if depth > 10:
            return False
        
        if isinstance(data, dict):
            for key, value in data.items():
                # Check keys too
                if isinstance(key, str) and detect_sql_injection(key):
                    return True
                if self._scan_for_injection(value, depth + 1):
                    return True
        
        elif isinstance(data, list):
            for item in data:
                if self._scan_for_injection(item, depth + 1):
                    return True
        
        elif isinstance(data, str):
            return detect_sql_injection(data)
        
        return False
