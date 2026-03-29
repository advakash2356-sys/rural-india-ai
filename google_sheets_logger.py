"""
Google Sheets Session Logger for FastAPI
Sends user login/logout events to Google Sheets via Google Apps Script Web App
Non-blocking, background task implementation
"""

import os
import asyncio
import logging
from typing import Optional, Dict
from datetime import datetime
import httpx
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== CONFIGURATION =====

# Your Google Apps Script Web App URL
# Format: https://script.google.com/macros/d/{SCRIPT_ID}/userweb?state=done
GOOGLE_SHEET_WEBHOOK_URL = os.getenv(
    'GOOGLE_SHEET_WEBHOOK_URL',
    'https://script.google.com/macros/d/YOUR_SCRIPT_ID_HERE/userweb?state=done'
)

# Timeout for requests to Google Sheets (in seconds)
SHEET_REQUEST_TIMEOUT = 5

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds


# ===== GOOGLE SHEETS LOGGER CLASS =====

class GoogleSheetLogger:
    """
    Manages communication with Google Sheets via Apps Script Web App
    Handles login/logout events with automatic calculation of session duration
    """
    
    def __init__(self, webhook_url: str = GOOGLE_SHEET_WEBHOOK_URL):
        """
        Initialize Google Sheets logger
        
        Args:
            webhook_url: URL of Google Apps Script Web App deployment
        """
        self.webhook_url = webhook_url
        self.timeout = SHEET_REQUEST_TIMEOUT
    
    async def log_login(self, user_email: str, user_name: str) -> bool:
        """
        Log user login event to Google Sheets
        
        Args:
            user_email: User's email address
            user_name: User's full name
            
        Returns:
            bool: True if logged successfully, False otherwise
        """
        payload = {
            'action': 'LOGIN',
            'email': user_email,
            'name': user_name,
            'timestamp': datetime.now().isoformat()
        }
        
        return await self._send_to_sheet(payload, user_email, 'LOGIN')
    
    async def log_logout(self, user_email: str) -> bool:
        """
        Log user logout event to Google Sheets
        
        Args:
            user_email: User's email address
            
        Returns:
            bool: True if logged successfully, False otherwise
        """
        payload = {
            'action': 'LOGOUT',
            'email': user_email,
            'timestamp': datetime.now().isoformat()
        }
        
        return await self._send_to_sheet(payload, user_email, 'LOGOUT')
    
    async def _send_to_sheet(self, payload: Dict, user_email: str, action: str) -> bool:
        """
        Send payload to Google Sheets with retry logic
        
        Args:
            payload: Data to send
            user_email: User email (for logging)
            action: 'LOGIN' or 'LOGOUT' (for logging)
            
        Returns:
            bool: True if successful, False if all retries failed
        """
        
        if not self.webhook_url or 'YOUR_SCRIPT_ID_HERE' in self.webhook_url:
            logger.warning(
                f"⚠️  {action} not logged: GOOGLE_SHEET_WEBHOOK_URL not configured. "
                "Set environment variable to enable Google Sheets logging."
            )
            return False
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        self.webhook_url,
                        json=payload,
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    if response.status_code in [200, 302]:  # 302 is redirect (success)
                        logger.info(
                            f"✅ {action} logged to Google Sheets: {user_email}"
                        )
                        return True
                    else:
                        logger.warning(
                            f"⚠️  {action} logging failed (attempt {attempt}/{MAX_RETRIES}): "
                            f"Status {response.status_code}"
                        )
                        
                        if attempt < MAX_RETRIES:
                            await asyncio.sleep(RETRY_DELAY)
                            continue
                        return False
                        
            except asyncio.TimeoutError:
                logger.warning(
                    f"⚠️  {action} logging timeout (attempt {attempt}/{MAX_RETRIES})"
                )
                
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_DELAY)
                    continue
                return False
                
            except Exception as e:
                logger.error(
                    f"❌ {action} logging error (attempt {attempt}/{MAX_RETRIES}): {str(e)}"
                )
                
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_DELAY)
                    continue
                return False
        
        return False


# ===== GLOBAL INSTANCE =====
sheet_logger = GoogleSheetLogger()


# ===== FASTAPI INTEGRATION FUNCTIONS =====

async def log_user_login_to_sheet(user_email: str, user_name: str) -> None:
    """
    Log user login to Google Sheets (async)
    
    Usage in FastAPI routes:
        @app.post("/login")
        async def login(user: Dict = Depends(verify_google_token)):
            await log_user_login_to_sheet(user['email'], user['name'])
            # ... rest of login logic
    
    Args:
        user_email: User's email
        user_name: User's full name
    """
    await sheet_logger.log_login(user_email, user_name)


async def log_user_logout_to_sheet(user_email: str) -> None:
    """
    Log user logout to Google Sheets (async)
    
    Usage in FastAPI routes:
        @app.post("/logout")
        async def logout(user: Dict = Depends(verify_google_token)):
            await log_user_logout_to_sheet(user['email'])
            # ... rest of logout logic
    
    Args:
        user_email: User's email
    """
    await sheet_logger.log_logout(user_email)


# ===== SYNCHRONOUS WRAPPER (for use in synchronous contexts) =====

def log_user_login_sync(user_email: str, user_name: str) -> None:
    """
    Synchronous wrapper for logging login
    Spawns async task in background
    
    Usage:
        log_user_login_sync(user['email'], user['name'])
    """
    asyncio.create_task(sheet_logger.log_login(user_email, user_name))


def log_user_logout_sync(user_email: str) -> None:
    """
    Synchronous wrapper for logging logout
    Spawns async task in background
    """
    asyncio.create_task(sheet_logger.log_logout(user_email))


# ===== INITIALIZATION =====

logger.info(f"🚀 Google Sheets Logger initialized")
if GOOGLE_SHEET_WEBHOOK_URL and 'YOUR_SCRIPT_ID_HERE' not in GOOGLE_SHEET_WEBHOOK_URL:
    logger.info(f"📊 Webhook URL configured: {GOOGLE_SHEET_WEBHOOK_URL[:50]}...")
else:
    logger.warning(
        "⚠️  GOOGLE_SHEET_WEBHOOK_URL not configured. "
        "Session logging to Google Sheets is disabled. "
        "Add GOOGLE_SHEET_WEBHOOK_URL to .env to enable."
    )
