"""
Authentication API Routes
JWT-based authentication for NCERT Doubt-Solver
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.db.models import UserCreate, UserLogin, UserResponse, TokenResponse
from app.db.mongodb import create_user, get_user_by_username, get_user_by_id

logger = logging.getLogger(__name__)

router = APIRouter()

# Password hashing - using argon2 (more secure and Windows-compatible)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    if not password:
        raise ValueError("Password cannot be empty")
    # Ensure password is a string and encode properly
    password_str = str(password)
    logger.debug(f"Hashing password of length: {len(password_str)}")
    return pwd_context.hash(password_str)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=settings.JWT_EXPIRY_HOURS))
    to_encode.update({"exp": expire})
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Ensure user is active"""
    if current_user.get("is_active") == False:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_role(required_role: str):
    """Dependency to require specific role"""
    async def role_checker(current_user: dict = Depends(get_current_active_user)):
        if current_user.get("role") != required_role and current_user.get("role") != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        return current_user
    return role_checker


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user"""
    
    try:
        # Check if user exists
        existing_user = await get_user_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Validate password
        if not user_data.password or len(user_data.password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters"
            )
        
        # Create user dictionary
        user_dict = {
            "username": user_data.username,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "grade": user_data.grade,
            "password": get_password_hash(user_data.password),
            "role": "student",
            "is_active": True
        }
        
        user_id = await create_user(user_dict)
        
        # Create token
        access_token = create_access_token(data={"sub": user_id})
        
        return TokenResponse(
            access_token=access_token,
            expires_in=settings.JWT_EXPIRY_HOURS * 3600,
            user=UserResponse(
                id=user_id,
                username=user_data.username,
                email=user_data.email,
                full_name=user_data.full_name,
                grade=user_data.grade,
                role="student",
                created_at=datetime.utcnow()
            )
        )
    except HTTPException:
        raise
    except RuntimeError as e:
        logger.error(f"Registration failed - Database error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database not available: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Registration failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get JWT token"""
    
    try:
        user = await get_user_by_username(form_data.username)
        
        if not user:
            logger.info(f"Login failed: user '{form_data.username}' not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not verify_password(form_data.password, user["password"]):
            logger.info(f"Login failed: incorrect password for '{form_data.username}'")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(data={"sub": str(user["_id"])})
        
        return TokenResponse(
            access_token=access_token,
            expires_in=settings.JWT_EXPIRY_HOURS * 3600,
            user=UserResponse(
                id=str(user["_id"]),
                username=user["username"],
                email=user.get("email", ""),
                full_name=user.get("full_name"),
                grade=user.get("grade"),
                role=user.get("role", "student"),
                created_at=user.get("created_at", datetime.utcnow())
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for user '{form_data.username}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_active_user)):
    """Get current user profile"""
    return UserResponse(
        id=str(current_user["_id"]),
        username=current_user["username"],
        email=current_user["email"],
        full_name=current_user.get("full_name"),
        grade=current_user.get("grade"),
        role=current_user.get("role", "student"),
        created_at=current_user.get("created_at", datetime.utcnow())
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(current_user: dict = Depends(get_current_active_user)):
    """Refresh JWT token"""
    access_token = create_access_token(data={"sub": str(current_user["_id"])})
    
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.JWT_EXPIRY_HOURS * 3600,
        user=UserResponse(
            id=str(current_user["_id"]),
            username=current_user["username"],
            email=current_user["email"],
            full_name=current_user.get("full_name"),
            grade=current_user.get("grade"),
            role=current_user.get("role", "student"),
            created_at=current_user.get("created_at", datetime.utcnow())
        )
    )
