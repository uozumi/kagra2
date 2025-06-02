from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Node関連モデル
class NodeBase(BaseModel):
    title: str
    description: Optional[str] = None
    type: str = "default"
    is_public: bool = False

class NodeCreate(NodeBase):
    pass

class NodeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    is_public: Optional[bool] = None

class Node(NodeBase):
    id: str
    created_at: datetime
    updated_at: datetime
    user_id: str
    parent_id: Optional[str] = None
    sort_order: int
    visibility_level: Optional[int] = None
    deleted_at: Optional[datetime] = None
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None

# Block関連モデル
class BlockBase(BaseModel):
    title: str
    content: Optional[str] = None

class BlockCreate(BlockBase):
    node_id: str
    block_theme_id: Optional[str] = None

class BlockUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    sort_order: Optional[int] = None
    block_theme_id: Optional[str] = None

class Block(BlockBase):
    id: str
    created_at: datetime
    updated_at: datetime
    user_id: str
    node_id: str
    block_theme_id: Optional[str] = None
    sort_order: Optional[int] = None
    deleted_at: Optional[datetime] = None
    node_title: Optional[str] = None
    user_name: Optional[str] = None

# BlockTheme関連モデル
class BlockThemeBase(BaseModel):
    title: str

class BlockThemeCreate(BlockThemeBase):
    pass

class BlockTheme(BlockThemeBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    creator_id: Optional[str] = None
    block_count: Optional[int] = 0

# その他のリクエスト/レスポンスモデル
class SetThemeRequest(BaseModel):
    theme_id: Optional[str] = None

class BlockReorderRequest(BaseModel):
    block_ids: list[str]

class ActivityItem(BaseModel):
    block_id: str
    block_title: str
    block_updated_at: datetime
    node_title: str
    user_name: str
    user_id: str
    node_id: str

class BlockCreateRequest(BaseModel):
    title: str
    content: Optional[str] = None
    node_id: str
    order_index: int
    block_theme_id: Optional[str] = None

class BlockUpdateRequest(BaseModel):
    title: str
    content: Optional[str] = None 