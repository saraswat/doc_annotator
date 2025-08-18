from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from authlib.integrations.httpx_client import AsyncOAuth2Client
import httpx
from datetime import datetime
from typing import Dict, Any

from app.core.database import get_async_session
from app.core.security import create_access_token, create_refresh_token, get_current_user, authenticate_user, get_password_hash, generate_password_reset_token
from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserResponse, UserCreate, UserPasswordLogin, UserPasswordReset

router = APIRouter()
security = HTTPBearer()

class OAuthProvider:
    """OAuth provider configurations"""
    
    @staticmethod
    def get_google_config():
        return {
            "client_id": settings.OAUTH_CLIENT_ID,
            "client_secret": settings.OAUTH_CLIENT_SECRET,
            "server_metadata_url": "https://accounts.google.com/.well-known/openid_configuration",
            "client_kwargs": {"scope": "openid email profile"}
        }
    
    @staticmethod
    def get_azure_config():
        return {
            "client_id": settings.OAUTH_CLIENT_ID,
            "client_secret": settings.OAUTH_CLIENT_SECRET,
            "server_metadata_url": f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/v2.0/.well-known/openid_configuration",
            "client_kwargs": {"scope": "openid email profile"}
        }
    
    @staticmethod
    def get_okta_config():
        return {
            "client_id": settings.OAUTH_CLIENT_ID,
            "client_secret": settings.OAUTH_CLIENT_SECRET,
            "server_metadata_url": f"https://{settings.OKTA_DOMAIN}/.well-known/openid_configuration",
            "client_kwargs": {"scope": "openid email profile"}
        }

async def get_oauth_client():
    """Get OAuth client based on configured provider"""
    if settings.OAUTH_PROVIDER == "google":
        config = OAuthProvider.get_google_config()
    elif settings.OAUTH_PROVIDER == "azure":
        config = OAuthProvider.get_azure_config()
    elif settings.OAUTH_PROVIDER == "okta":
        config = OAuthProvider.get_okta_config()
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth provider not configured"
        )
    
    client = AsyncOAuth2Client(
        client_id=config["client_id"],
        client_secret=config["client_secret"]
    )
    return client, config

@router.get("/login")
async def login():
    """Initiate OAuth login flow"""
    try:
        client, config = await get_oauth_client()
        
        # Get authorization server metadata
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(config["server_metadata_url"])
            response.raise_for_status()
            metadata = response.json()
        
        authorization_url = await client.create_authorization_url(
            metadata["authorization_endpoint"],
            redirect_uri=settings.OAUTH_REDIRECT_URI,
            scope=config["client_kwargs"]["scope"]
        )
        
        return {"authorization_url": authorization_url[0], "state": authorization_url[1]}
    except Exception as e:
        # Fallback to hardcoded Google OAuth URLs
        import secrets
        state = secrets.token_urlsafe(32)
        
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={settings.OAUTH_CLIENT_ID}&"
            f"redirect_uri={settings.OAUTH_REDIRECT_URI}&"
            f"scope=openid%20email%20profile&"
            f"response_type=code&"
            f"state={state}"
        )
        
        return {"authorization_url": auth_url, "state": state}

@router.post("/callback")
async def oauth_callback(
    code: str = Form(...),
    state: str = Form(...),
    db: AsyncSession = Depends(get_async_session)
):
    """Handle OAuth callback and create/login user"""
    try:
        print(f"OAuth callback received - Code: {code[:20]}..., State: {state}")
        client, config = await get_oauth_client()
        
        # Use hardcoded Google OAuth endpoints (more reliable)
        token_endpoint = "https://oauth2.googleapis.com/token"
        userinfo_endpoint = "https://openidconnect.googleapis.com/v1/userinfo"
        
        # Exchange code for token using direct HTTP request
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            token_response = await http_client.post(
                token_endpoint,
                data={
                    "client_id": settings.OAUTH_CLIENT_ID,
                    "client_secret": settings.OAUTH_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.OAUTH_REDIRECT_URI,
                }
            )
            
            if token_response.status_code == 400:
                error_data = token_response.json()
                print(f"Token exchange error: {error_data}")
                if error_data.get("error") == "invalid_grant":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Authorization code has expired or been used already"
                    )
            
            token_response.raise_for_status()
            token_data = token_response.json()
        
        # Get user info
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            headers = {"Authorization": f"Bearer {token_data['access_token']}"}
            user_response = await http_client.get(userinfo_endpoint, headers=headers)
            user_response.raise_for_status()
            user_info = user_response.json()
        
        # Create or get user
        user = await get_or_create_user(db, user_info, settings.OAUTH_PROVIDER)
        
        # Generate tokens
        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)
        
        # Update last login
        user.last_login = datetime.utcnow()
        await db.commit()
        await db.refresh(user)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": UserResponse.from_orm(user)
        }
        
    except Exception as e:
        print(f"OAuth callback error: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth callback failed: {str(e)}"
        )

async def get_or_create_user(
    db: AsyncSession, 
    user_info: Dict[str, Any], 
    provider: str
) -> User:
    """Get existing user or create new one from OAuth info"""
    
    # Extract user data based on provider
    if provider == "google":
        oauth_id = user_info["sub"]
        email = user_info["email"]
        name = user_info["name"]
        avatar_url = user_info.get("picture")
    elif provider == "azure":
        oauth_id = user_info["sub"]
        email = user_info["email"]
        name = user_info["name"]
        avatar_url = None
    elif provider == "okta":
        oauth_id = user_info["sub"]
        email = user_info["email"]
        name = user_info["name"]
        avatar_url = None
    else:
        raise ValueError(f"Unsupported OAuth provider: {provider}")
    
    # Check if user exists
    result = await db.execute(
        select(User).where(
            User.oauth_provider == provider,
            User.oauth_id == oauth_id
        )
    )
    user = result.scalar_one_or_none()
    
    if user:
        # Update user info if changed
        user.email = email
        user.name = name
        if avatar_url:
            user.avatar_url = avatar_url
        await db.commit()
        await db.refresh(user)
        return user
    
    # Create new user
    user_create = UserCreate(
        email=email,
        name=name,
        avatar_url=avatar_url,
        oauth_provider=provider,
        oauth_id=oauth_id
    )
    
    user = User(**user_create.dict())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user

@router.post("/refresh")
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token"""
    from app.core.security import verify_token
    
    user_id = verify_token(refresh_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Generate new access token
    access_token = create_access_token(subject=user_id)
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse.from_orm(current_user)

@router.post("/logout")
async def logout():
    """Logout user (client should delete tokens)"""
    return {"message": "Logged out successfully"}

@router.post("/login/password")
async def login_with_password(
    user_data: UserPasswordLogin,
    db: AsyncSession = Depends(get_async_session)
):
    """Login with email and password"""
    user = await authenticate_user(user_data.email, user_data.password, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )
    
    # Generate tokens
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user),
        "password_reset_required": user.password_reset_required
    }

@router.post("/password/change")
async def change_password(
    password_data: UserPasswordReset,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Change user's password"""
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    current_user.password_reset_required = False
    current_user.password_reset_token = None
    current_user.password_reset_expires = None
    
    await db.commit()
    await db.refresh(current_user)
    
    return {"message": "Password changed successfully"}

@router.get("/debug/cookies")
async def debug_cookies(request: Request):
    """Debug endpoint to check cookies and headers without authentication"""
    crisp_user_cookie = request.cookies.get("crisp_user")
    crisp_user_header = request.headers.get("x-crisp-user")
    
    return {
        "cookies": dict(request.cookies),
        "headers": dict(request.headers),
        "client": str(request.client),
        "url": str(request.url),
        "crisp_user_cookie": crisp_user_cookie,
        "crisp_user_header": crisp_user_header,
        "crisp_user_final": crisp_user_cookie or crisp_user_header
    }

@router.get("/login/cookie")
async def login_with_cookie(
    request: Request,
    db: AsyncSession = Depends(get_async_session)
):
    """Login using crisp_user cookie for intranet environments"""
    print(f"🔍 Cookie authentication request received from: {request.client.host}")
    print(f"🍪 All cookies: {dict(request.cookies)}")
    print(f"📋 All headers: {dict(request.headers)}")
    
    # Get crisp_user from cookie or header
    crisp_user = request.cookies.get("crisp_user") or request.headers.get("x-crisp-user")
    
    print(f"🍪 Cookie authentication attempt - crisp_user value: '{crisp_user}'")
    
    if not crisp_user:
        print("❌ Cookie authentication failed - No crisp_user cookie or header found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No crisp_user cookie or header found"
        )
    
    # Check if user exists
    result = await db.execute(
        select(User).where(User.email == crisp_user)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Create new user automatically for intranet authentication
        user_name = crisp_user.split('@')[0] if '@' in crisp_user else crisp_user
        print(f"👤 Creating new user for crisp_user: {crisp_user} (name: {user_name})")
        
        user = User(
            email=crisp_user,
            name=user_name,
            oauth_provider="intranet",
            oauth_id=crisp_user,
            is_active=True,
            password_reset_required=False
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        print(f"✅ User created successfully - ID: {user.id}, Name: {user.name}")
    else:
        print(f"🔍 Found existing user - ID: {user.id}, Name: {user.name}, Email: {user.email}")
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )
    
    # Generate tokens
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    
    print(f"🎉 Cookie authentication successful for user: {user.name} ({user.email})")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user),
        "password_reset_required": False
    }