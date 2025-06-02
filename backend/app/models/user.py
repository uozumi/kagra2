"""
ユーザー関連のPydanticモデル定義

認証、ユーザー管理、プロフィール情報などで使用されるデータモデルを定義します。
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class UserBase(BaseModel):
    """ユーザーの基本モデル"""
    email: EmailStr = Field(..., description="メールアドレス")
    display_name: str = Field(..., description="表示名")


class UserCreate(UserBase):
    """ユーザー作成用モデル"""
    password: str = Field(..., description="パスワード")


class UserLogin(BaseModel):
    """ユーザーログイン用モデル"""
    email: EmailStr = Field(..., description="メールアドレス")
    password: str = Field(..., description="パスワード")


class UserUpdate(BaseModel):
    """ユーザー情報更新用モデル"""
    display_name: Optional[str] = Field(None, description="表示名")
    email: Optional[EmailStr] = Field(None, description="メールアドレス")


class UserUpdateRequest(BaseModel):
    """ユーザー情報更新リクエスト用モデル"""
    name: str = Field(..., description="ユーザー名")
    slack_member_id: Optional[str] = Field(None, description="SlackメンバーID")
    extension_number: Optional[str] = Field(None, description="内線番号")


class AffiliationInfo(BaseModel):
    """所属情報モデル"""
    tenantId: str = Field(..., description="テナントID")
    tenantName: str = Field(..., description="テナント名")
    departments: List[str] = Field(default_factory=list, description="所属部署リスト")


class UserResponse(BaseModel):
    """ユーザー情報レスポンス用モデル"""
    id: str = Field(..., description="ユーザーID")
    email: EmailStr = Field(..., description="メールアドレス")
    display_name: Optional[str] = Field(None, description="表示名")
    role: str = Field(default="editor", description="ユーザーロール")
    avatar_url: Optional[str] = Field(None, description="アバター画像URL")
    name: Optional[str] = Field(None, description="ユーザー名")
    slack_member_id: Optional[str] = Field(None, description="SlackメンバーID")
    extension_number: Optional[str] = Field(None, description="内線番号")
    affiliations: List[AffiliationInfo] = Field(default_factory=list, description="所属情報リスト")
    
    class Config:
        from_attributes = True


class User(BaseModel):
    """Supabaseユーザー情報を表現するモデル"""
    id: str = Field(..., description="ユーザーID")
    email: str = Field(..., description="メールアドレス")
    display_name: Optional[str] = Field(None, description="表示名")
    role: str = Field(default="editor", description="ユーザーロール")
    created_at: Optional[str] = Field(None, description="作成日時")
    updated_at: Optional[str] = Field(None, description="更新日時")
    email_confirmed_at: Optional[str] = Field(None, description="メール確認日時")
    last_sign_in_at: Optional[str] = Field(None, description="最終ログイン日時")
    raw_app_meta_data: Optional[Dict[str, Any]] = Field(None, description="アプリメタデータ")
    raw_user_meta_data: Optional[Dict[str, Any]] = Field(None, description="ユーザーメタデータ")
    is_anonymous: bool = Field(default=False, description="匿名ユーザーフラグ")
    
    class Config:
        from_attributes = True 