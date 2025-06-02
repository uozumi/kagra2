from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ThemeBase(BaseModel):
    """テーマの基本モデル"""
    title: str
    description: Optional[str] = None


class ThemeCreate(ThemeBase):
    """テーマ作成用モデル"""
    pass


class ThemeUpdate(BaseModel):
    """テーマ更新用モデル"""
    title: Optional[str] = None
    description: Optional[str] = None


class ThemeResponse(ThemeBase):
    """テーマレスポンス用モデル"""
    id: str
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 