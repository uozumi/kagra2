from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    display_name: str


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """ユーザー情報更新用モデル"""
    display_name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserUpdateRequest(BaseModel):
    """ユーザー情報更新リクエスト用モデル"""
    name: str
    slack_member_id: Optional[str] = None
    extension_number: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    display_name: Optional[str] = None
    role: str = "editor"
    
    class Config:
        from_attributes = True


class User(BaseModel):
    """Supabaseユーザー情報を表現するモデル"""
    id: str
    email: str
    display_name: Optional[str] = None
    role: str = "editor"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    email_confirmed_at: Optional[str] = None
    last_sign_in_at: Optional[str] = None
    raw_app_meta_data: Optional[Dict[str, Any]] = None
    raw_user_meta_data: Optional[Dict[str, Any]] = None
    is_anonymous: bool = False
    
    class Config:
        from_attributes = True 