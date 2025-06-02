"""
テーマ関連のPydanticモデル定義

ブロックテーマシステムで使用されるデータモデルを定義します。
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ThemeBase(BaseModel):
    """テーマの基本モデル"""
    title: str = Field(..., description="テーマのタイトル")
    description: Optional[str] = Field(None, description="テーマの説明")


class ThemeCreate(ThemeBase):
    """テーマ作成用モデル"""
    pass


class ThemeUpdate(BaseModel):
    """テーマ更新用モデル"""
    title: Optional[str] = Field(None, description="テーマのタイトル")
    description: Optional[str] = Field(None, description="テーマの説明")


class Theme(ThemeBase):
    """テーマの完全なモデル（データベースから取得）"""
    id: str = Field(..., description="テーマID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
    creator_id: Optional[str] = Field(None, description="作成者のユーザーID")
    block_count: Optional[int] = Field(default=0, description="関連ブロック数")

    class Config:
        from_attributes = True


class ThemeResponse(ThemeBase):
    """テーマレスポンス用モデル（API応答用）"""
    id: str = Field(..., description="テーマID")
    created_by: str = Field(..., description="作成者のユーザーID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
    block_count: Optional[int] = Field(default=0, description="関連ブロック数")

    class Config:
        from_attributes = True 