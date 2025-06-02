"""
Charaxy関連のPydanticモデル定義

ノード、ブロック、アクティビティなどのCharaxyシステムで使用されるデータモデルを定義します。
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ===== Node関連モデル =====

class NodeBase(BaseModel):
    """ノードの基本モデル"""
    title: str = Field(..., description="ノードのタイトル")
    description: Optional[str] = Field(None, description="ノードの説明")
    type: str = Field(default="default", description="ノードのタイプ")
    is_public: bool = Field(default=False, description="公開フラグ")


class NodeCreate(NodeBase):
    """ノード作成用モデル"""
    pass


class NodeUpdate(BaseModel):
    """ノード更新用モデル"""
    title: Optional[str] = Field(None, description="ノードのタイトル")
    description: Optional[str] = Field(None, description="ノードの説明")
    type: Optional[str] = Field(None, description="ノードのタイプ")
    is_public: Optional[bool] = Field(None, description="公開フラグ")


class Node(NodeBase):
    """ノードの完全なモデル（データベースから取得）"""
    id: str = Field(..., description="ノードID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
    user_id: str = Field(..., description="作成者のユーザーID")
    parent_id: Optional[str] = Field(None, description="親ノードID")
    sort_order: int = Field(..., description="ソート順")
    visibility_level: Optional[int] = Field(None, description="可視性レベル")
    deleted_at: Optional[datetime] = Field(None, description="削除日時")
    
    # 関連データ（JOIN結果）
    user_name: Optional[str] = Field(None, description="作成者名")
    user_avatar: Optional[str] = Field(None, description="作成者のアバター")

    class Config:
        from_attributes = True


# ===== Block関連モデル =====

class BlockBase(BaseModel):
    """ブロックの基本モデル"""
    title: str = Field(..., description="ブロックのタイトル")
    content: Optional[str] = Field(None, description="ブロックの内容")


class BlockCreate(BlockBase):
    """ブロック作成用モデル"""
    node_id: str = Field(..., description="所属するノードID")
    block_theme_id: Optional[str] = Field(None, description="ブロックテーマID")


class BlockUpdate(BaseModel):
    """ブロック更新用モデル"""
    title: Optional[str] = Field(None, description="ブロックのタイトル")
    content: Optional[str] = Field(None, description="ブロックの内容")
    sort_order: Optional[int] = Field(None, description="ソート順")
    block_theme_id: Optional[str] = Field(None, description="ブロックテーマID")


class Block(BlockBase):
    """ブロックの完全なモデル（データベースから取得）"""
    id: str = Field(..., description="ブロックID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
    user_id: str = Field(..., description="作成者のユーザーID")
    node_id: str = Field(..., description="所属するノードID")
    block_theme_id: Optional[str] = Field(None, description="ブロックテーマID")
    sort_order: Optional[int] = Field(None, description="ソート順")
    deleted_at: Optional[datetime] = Field(None, description="削除日時")
    
    # 関連データ（JOIN結果）
    node_title: Optional[str] = Field(None, description="所属ノードのタイトル")
    user_name: Optional[str] = Field(None, description="作成者名")

    class Config:
        from_attributes = True


# ===== リクエスト/レスポンス用モデル =====

class BlockCreateRequest(BaseModel):
    """ブロック作成リクエスト用モデル"""
    title: str = Field(..., description="ブロックのタイトル")
    content: Optional[str] = Field(None, description="ブロックの内容")
    node_id: str = Field(..., description="所属するノードID")
    order_index: int = Field(..., description="挿入位置のインデックス")
    block_theme_id: Optional[str] = Field(None, description="ブロックテーマID")


class BlockUpdateRequest(BaseModel):
    """ブロック更新リクエスト用モデル"""
    title: str = Field(..., description="ブロックのタイトル")
    content: Optional[str] = Field(None, description="ブロックの内容")


class BlockReorderRequest(BaseModel):
    """ブロック並び替えリクエスト用モデル"""
    block_ids: List[str] = Field(..., description="並び替え後のブロックIDリスト")


class SetThemeRequest(BaseModel):
    """テーマ設定リクエスト用モデル"""
    theme_id: Optional[str] = Field(None, description="設定するテーマID（Noneで解除）")


# ===== アクティビティ関連モデル =====

class ActivityItem(BaseModel):
    """アクティビティアイテムモデル"""
    block_id: str = Field(..., description="ブロックID")
    block_title: str = Field(..., description="ブロックのタイトル")
    block_updated_at: datetime = Field(..., description="ブロックの更新日時")
    node_title: str = Field(..., description="所属ノードのタイトル")
    user_name: str = Field(..., description="更新者名")
    user_id: str = Field(..., description="更新者のユーザーID")
    node_id: str = Field(..., description="所属ノードID")

    class Config:
        from_attributes = True 