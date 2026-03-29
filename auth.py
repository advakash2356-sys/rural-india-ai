"""
Google OAuth2 Authentication & Security Middleware for Rural India AI
Handles JWT verification, audit logging, and rate limiting
"""

import os
import time
import logging
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Optional, Dict, Tuple

from fastapi import HTTPException, status, Header
from google.auth.transport import requests
from google.oauth2 import id_token
import dotenv

# Load environment variables
dotenv.load_dotenv()

# ===== CONFIGURATION =====
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
if not GOOGLE_CLIENT_ID:
    raise ValueError("❌ GOOGLE_CLIENT_ID environment variable is not set!")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('data/logs/auth.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ===== AUDIT LOGGING =====

class AuditLogger:
    """
    Centralized audit logging for all authenticated interactions
    Format: [Timestamp] | User: [email] | Endpoint: [route] | Query: [text]
    """
    
    @staticmethod
    def log_interaction(user_email: str, endpoint: str, query: Optional[str] = None, 
                       method: str = 'POST', status_code: int = 200):
        """
        Log an authenticated interaction to audit trail
        """
        timestamp = datetime.now().isoformat()
        query_text = query[:100] if query else '[no query]'  # Truncate long queries
        
        log_message = (
            f"[{timestamp}] | User: {user_email} | Endpoint: {endpoint} | "
            f"Method: {method} | Status: {status_code} | Query: {query_text}"
        )
        
        logger.info(log_message)
    
    @staticmethod
    def log_auth_event(event_type: str, user_email: Optional[str] = None, result: str = 'success'):
        """
        Log authentication events (login, logout, token refresh, etc.)
        """
        timestamp = datetime.now().isoformat()
        user_info = f" | User: {user_email}" if user_email else ""
        
        log_message = f"[{timestamp}] | EVENT: {event_type}{user_info} | Result: {result}"
        logger.info(log_message)
    
    @staticmethod
    def log_error(error_type: str, details: str, user_email: Optional[str] = None):
        """
        Log security-related errors
        """
        timestamp = datetime.now().isoformat()
        user_info = f" | User: {user_email}" if user_email else ""
        
        log_message = f"[{timestamp}] | ERROR: {error_type}{user_info} | Details: {details}"
        logger.error(log_message)


# ===== RATE LIMITING =====

class RateLimiter:
    """
    Token-bucket rate limiter keyed by user email
    Prevents spam from authenticated users
    """
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.refill_rate = requests_per_minute / 60  # Tokens per second
        self.user_buckets: Dict[str, Dict] = {}
    
    def is_allowed(self, user_email: str) -> Tuple[bool, Dict]:
        """
        Check if user is allowed to make a request
        Returns (allowed: bool, info: dict with remaining tokens)
        """
        now = time.time()
        
        # Initialize bucket for new user
        if user_email not in self.user_buckets:
            self.user_buckets[user_email] = {
                'tokens': self.requests_per_minute,
                'last_update': now
            }
        
        bucket = self.user_buckets[user_email]
        
        # Refill tokens based on elapsed time
        elapsed = now - bucket['last_update']
        tokens_to_add = elapsed * self.refill_rate
        bucket['tokens'] = min(
            self.requests_per_minute,
            bucket['tokens'] + tokens_to_add
        )
        bucket['last_update'] = now
        
        # Check if user has tokens available
        if bucket['tokens'] >= 1:
            bucket['tokens'] -= 1
            return True, {
                'remaining': int(bucket['tokens']),
                'reset_in_seconds': int((self.requests_per_minute - bucket['tokens']) / self.refill_rate)
            }
        else:
            return False, {
                'remaining': 0,
                'reset_in_seconds': int(1 / self.refill_rate)
            }


# ===== JWT VERIFICATION =====

class GoogleTokenVerifier:
    """
    Verifies Google OAuth2 JWT tokens and extracts user information
    """
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.request = requests.Request()
    
    def verify_token(self, token: str) -> Dict:
        """
        Verify JWT token and return decoded payload
        
        Args:
            token: JWT token from Google OAuth2
            
        Returns:
            Dict with decoded token payload (email, name, picture, etc.)
            
        Raises:
            HTTPException: If token is invalid or verification fails
        """
        try:
            # Verify token with Google
            idinfo = id_token.verify_oauth2_token(
                token,
                self.request,
                self.client_id
            )
            
            # Verify token is not expired (built-in to verify_oauth2_token)
            # Verify token is for our app
            if idinfo['aud'] != self.client_id:
                raise ValueError('Token audience mismatch')
            
            logger.info(f"✅ Token verified for user: {idinfo.get('email')}")
            
            return {
                'email': idinfo.get('email'),
                'name': idinfo.get('name'),
                'picture': idinfo.get('picture'),
                'iss': idinfo.get('iss'),
                'iat': idinfo.get('iat'),
                'exp': idinfo.get('exp')
            }
            
        except ValueError as e:
            error_msg = f'Invalid token: {str(e)}'
            logger.error(f"❌ {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_msg,
                headers={'WWW-Authenticate': 'Bearer'},
            )
        except Exception as e:
            error_msg = f'Token verification failed: {str(e)}'
            logger.error(f"❌ {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_msg,
                headers={'WWW-Authenticate': 'Bearer'},
            )


# ===== DEPENDENCY INJECTION =====

# Initialize global instances
verifier = GoogleTokenVerifier(GOOGLE_CLIENT_ID)
rate_limiter = RateLimiter(requests_per_minute=60)  # 60 requests per minute per user


async def verify_google_token(authorization: Optional[str] = Header(None)) -> Dict:
    """
    FastAPI dependency to verify Google OAuth2 JWT token
    
    Usage in routes:
        @app.post("/api/v4/agents/query")
        async def query_agents(query: str, user: Dict = Depends(verify_google_token)):
            # user contains: email, name, picture, etc.
            pass
    
    Args:
        authorization: Header value like "Bearer <token>"
        
    Returns:
        Dict with user info (email, name, picture, etc.)
        
    Raises:
        HTTPException 401: If token is missing or invalid
    """
    
    # Check if Authorization header is present
    if not authorization:
        logger.warning("⚠️ Missing Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Missing Authorization header',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    
    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        logger.warning(f"⚠️ Invalid Authorization header format: {authorization[:20]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid Authorization header format. Use "Bearer <token>"',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    
    token = parts[1]
    
    # Verify token
    user_info = verifier.verify_token(token)
    
    logger.info(f"🔐 User authenticated: {user_info['email']}")
    
    return user_info


async def verify_google_token_with_rate_limit(
    user: Dict = Depends(verify_google_token)
) -> Dict:
    """
    Enhanced dependency that includes rate limiting
    
    Usage in routes:
        @app.post("/api/v4/agents/query")
        async def query_agents(query: str, user: Dict = Depends(verify_google_token_with_rate_limit)):
            pass
    
    Args:
        user: Dict from verify_google_token
        
    Returns:
        Dict with user info
        
    Raises:
        HTTPException 429: If user exceeds rate limit
    """
    
    email = user.get('email')
    allowed, info = rate_limiter.is_allowed(email)
    
    if not allowed:
        logger.warning(
            f"⚠️ Rate limit exceeded for user: {email} | "
            f"Reset in {info['reset_in_seconds']}s"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                'error': 'Rate limit exceeded',
                'reset_in_seconds': info['reset_in_seconds'],
                'limit': rate_limiter.requests_per_minute,
                'window': 'per minute'
            }
        )
    
    # Attach rate limit info to user dict for logging
    user['rate_limit_remaining'] = info['remaining']
    
    return user


# ===== HELPER FUNCTIONS =====

def create_audit_log_dir():
    """
    Ensure data/logs directory exists
    """
    os.makedirs('data/logs', exist_ok=True)


# Initialize on import
create_audit_log_dir()
logger.info(f"🚀 Authentication system initialized with Google Client ID: {GOOGLE_CLIENT_ID[:20]}...")
