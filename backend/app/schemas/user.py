from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    name: str
    avatar_url: Optional[str] = None

class UserCreate(UserBase):
    oauth_provider: Optional[str] = None
    oauth_id: Optional[str] = None

class UserCreateByAdmin(UserBase):
    password: str
    is_admin: Optional[bool] = False

class UserPasswordLogin(BaseModel):
    email: EmailStr
    password: str

class UserPasswordReset(BaseModel):
    email: Optional[EmailStr] = None
    new_password: str
    reset_token: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    avatar_url: Optional[str] = None

class UserInDBBase(UserBase):
    id: int
    oauth_provider: Optional[str] = None
    oauth_id: Optional[str] = None
    is_active: bool
    is_admin: bool
    password_reset_required: bool = False
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class User(UserInDBBase):
    pass

class UserResponse(BaseModel):
    # Convert snake_case to camelCase for frontend
    id: int
    email: EmailStr
    name: str
    avatarUrl: Optional[str] = Field(alias="avatar_url", serialization_alias="avatarUrl")
    oauthProvider: Optional[str] = Field(alias="oauth_provider", serialization_alias="oauthProvider")
    oauthId: Optional[str] = Field(alias="oauth_id", serialization_alias="oauthId")
    isActive: bool = Field(alias="is_active", serialization_alias="isActive")
    isAdmin: bool = Field(alias="is_admin", serialization_alias="isAdmin")
    passwordResetRequired: bool = Field(alias="password_reset_required", serialization_alias="passwordResetRequired")
    createdAt: datetime = Field(alias="created_at", serialization_alias="createdAt")
    lastLogin: Optional[datetime] = Field(alias="last_login", serialization_alias="lastLogin")
    
    class Config:
        from_attributes = True
        populate_by_name = True