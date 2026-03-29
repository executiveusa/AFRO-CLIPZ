"""
AfroMations - Auth Layer
JWT tokens + optional Google OAuth.
Works standalone (email magic-link style) OR with Google credentials.
"""
import os
import secrets
import hashlib
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

try:
    from jose import JWTError, jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

SECRET_KEY = os.environ.get("SESSION_SECRET") or secrets.token_hex(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.environ.get("TOKEN_EXPIRE_HOURS", 72))

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8080/auth/google/callback")

bearer_scheme = HTTPBearer(auto_error=False)


# ─── JWT ──────────────────────────────────────────────────────────────────────

def create_access_token(user_id: str, email: str, plan: str = "free") -> str:
    if not JWT_AVAILABLE:
        # Fallback: simple signed token
        payload = f"{user_id}:{email}:{plan}"
        sig = hashlib.sha256(f"{payload}{SECRET_KEY}".encode()).hexdigest()[:16]
        return f"{payload}:{sig}"
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    return jwt.encode(
        {"sub": user_id, "email": email, "plan": plan, "exp": expire},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_token(token: str) -> Optional[Dict]:
    if not JWT_AVAILABLE:
        # Fallback verification
        try:
            parts = token.rsplit(":", 1)
            payload, sig = parts[0], parts[1]
            expected = hashlib.sha256(f"{payload}{SECRET_KEY}".encode()).hexdigest()[:16]
            if sig != expected:
                return None
            uid, email, plan = payload.split(":", 2)
            return {"sub": uid, "email": email, "plan": plan}
        except Exception:
            return None
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    request: Request = None,
) -> Optional[Dict]:
    """Extract user from Bearer token or cookie. Returns None if not auth'd."""
    token = None
    if credentials:
        token = credentials.credentials
    elif request:
        token = request.cookies.get("access_token")

    if not token:
        return None
    return decode_token(token)


async def require_user(
    user: Optional[Dict] = Depends(get_current_user),
) -> Dict:
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# ─── Google OAuth ─────────────────────────────────────────────────────────────

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def google_oauth_available() -> bool:
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)


def get_google_auth_url(state: str = None) -> str:
    if not google_oauth_available():
        raise HTTPException(status_code=501, detail="Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.")
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "state": state or secrets.token_hex(16),
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{GOOGLE_AUTH_URL}?{query}"


async def exchange_google_code(code: str) -> Dict:
    """Exchange authorization code for user info."""
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        })
        token_resp.raise_for_status()
        tokens = token_resp.json()

        user_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        user_resp.raise_for_status()
        return user_resp.json()
