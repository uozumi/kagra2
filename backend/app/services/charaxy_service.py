"""
Charaxyサービス

Charaxyシステムのビジネスロジックを提供します。
ノード、ブロック、テーマ、アクティビティの管理機能を含みます。
"""

from typing import List, Optional, Dict, Any, Tuple
from fastapi import HTTPException
from datetime import datetime
import structlog

from app.models.user import User
from app.models.charaxy import Node, Block, ActivityItem

logger = structlog.get_logger()


class CharaxyService:
    """Charaxyサービスクラス
    
    ノード、ブロック、テーマ、アクティビティの管理機能を提供します。
    """
    
    def __init__(self, supabase) -> None:
        """Charaxyサービスを初期化
        
        Args:
            supabase: Supabaseクライアント
        """
        self.supabase = supabase
    
    # ===== 権限チェック =====
    
    def _check_ownership(self, table_name: str, resource_id: str, user_id: str, user_field: str = 'user_id') -> bool:
        """リソースの所有者チェック
        
        Args:
            table_name: テーブル名
            resource_id: リソースID
            user_id: ユーザーID
            user_field: ユーザーIDフィールド名
            
        Returns:
            所有者の場合True
        """
        try:
            response = self.supabase.table(table_name).select(user_field).eq('id', resource_id)
            
            # 論理削除対応
            if table_name in ['nodes', 'blocks']:
                response = response.is_('deleted_at', 'null')
            
            result = response.single().execute()
            return result.data and result.data[user_field] == user_id
            
        except Exception as e:
            logger.error("所有者チェックエラー", table=table_name, resource_id=resource_id, error=str(e))
            return False
    
    def _is_admin_user(self, user_id: str) -> bool:
        """管理者権限チェック
        
        Args:
            user_id: ユーザーID
            
        Returns:
            管理者の場合True
        """
        try:
            response = self.supabase.table('user_system_permissions').select('permission_level').eq('user_id', user_id).eq('permission_level', 1).execute()
            return bool(response.data)
        except Exception as e:
            logger.error("管理者権限チェックエラー", user_id=user_id, error=str(e))
            return False
    
    def check_node_ownership_or_admin(self, node_id: str, user_id: str) -> Tuple[bool, str]:
        """ノードの所有者または管理者権限チェック
        
        Args:
            node_id: ノードID
            user_id: ユーザーID
            
        Returns:
            (権限あり, 理由)のタプル
        """
        try:
            response = self.supabase.table('nodes').select('user_id').eq('id', node_id).is_('deleted_at', 'null').single().execute()
            
            if not response.data:
                return False, "ノードが見つかりません"
            
            node_owner_id = response.data['user_id']
            
            # 所有者チェック
            if node_owner_id == user_id:
                return True, "所有者"
            
            # 管理者権限チェック
            if self._is_admin_user(user_id):
                return True, "管理者権限"
            
            return False, f"権限なし（所有者: {node_owner_id}）"
            
        except Exception as e:
            logger.error("ノード権限チェックエラー", node_id=node_id, user_id=user_id, error=str(e))
            return False, f"権限チェックエラー: {str(e)}"
    
    def check_node_ownership(self, node_id: str, user_id: str) -> bool:
        """ノードの所有者チェック（後方互換性）"""
        has_permission, _ = self.check_node_ownership_or_admin(node_id, user_id)
        return has_permission
    
    def check_block_ownership(self, block_id: str, user_id: str) -> bool:
        """ブロックの所有者チェック"""
        return self._check_ownership('blocks', block_id, user_id)
    
    def check_theme_ownership(self, theme_id: str, user_id: str) -> bool:
        """テーマの所有者チェック"""
        return self._check_ownership('block_themes', theme_id, user_id, 'creator_id')
    
    # ===== ノード管理 =====
    
    def get_user_nodes(self, user_id: str) -> List[Dict[str, Any]]:
        """ユーザーのノード一覧取得"""
        response = self.supabase.table('nodes').select('*').eq('user_id', user_id).eq('type', 'charaxy').is_('deleted_at', 'null').order('updated_at', desc=True).execute()
        return response.data or []
    
    def get_nodes_filtered(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """フィルタリング済みノード一覧取得"""
        response = self.supabase.table('nodes').select('*').or_(f'user_id.eq.{user_id},is_public.eq.true').is_('deleted_at', 'null').order('updated_at', desc=True).range(skip, skip + limit - 1).execute()
        return response.data or []
    
    def get_node_by_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        """IDによるノード取得"""
        try:
            response = self.supabase.table('nodes').select('*').eq('id', node_id).is_('deleted_at', 'null').single().execute()
            return response.data if response.data else None
        except Exception as e:
            logger.error("ノード取得エラー", node_id=node_id, error=str(e))
            return None
    
    def get_node_with_user_info(self, node_id: str) -> Optional[Dict[str, Any]]:
        """ユーザー情報付きノード取得"""
        try:
            # ノード基本情報を取得
            response = self.supabase.table('nodes').select('*').eq('id', node_id).is_('deleted_at', 'null').single().execute()
            
            if not response.data:
                return None
            
            node_data = response.data
            
            # ユーザー情報を追加
            if node_data.get('user_id'):
                user_info = self._get_user_info(node_data['user_id'])
                node_data.update(user_info)
            
            return node_data
            
        except Exception as e:
            logger.error("ユーザー情報付きノード取得エラー", node_id=node_id, error=str(e))
            return None
    
    def _get_user_info(self, user_id: str) -> Dict[str, Any]:
        """ユーザー情報取得（内部メソッド）"""
        user_info = {
            'user_name': None,
            'user_avatar': None,
            'user_affiliations': []
        }
        
        try:
            # ユーザー名取得
            user_response = self.supabase.table('users').select('name').eq('id', user_id).execute()
            if user_response.data and user_response.data[0].get('name'):
                user_info['user_name'] = user_response.data[0]['name']
            
            # アバター取得
            avatar_response = self.supabase.table('user_profiles_view').select('avatar_url').eq('id', user_id).execute()
            if avatar_response.data and avatar_response.data[0].get('avatar_url'):
                user_info['user_avatar'] = avatar_response.data[0]['avatar_url']
            
            # 所属情報取得
            affiliations_response = self.supabase.table('user_affiliations').select('*').eq('user_id', user_id).execute()
            if affiliations_response.data:
                tenant_groups = {}
                for aff in affiliations_response.data:
                    tenant_id = aff['tenant_id']
                    if tenant_id not in tenant_groups:
                        tenant_groups[tenant_id] = {
                            'tenantId': tenant_id,
                            'tenantName': aff['tenant_name'],
                            'departments': []
                        }
                    if aff.get('department_name'):
                        tenant_groups[tenant_id]['departments'].append(aff['department_name'])
                
                user_info['user_affiliations'] = list(tenant_groups.values())
            
        except Exception as e:
            logger.warning("ユーザー情報取得エラー", user_id=user_id, error=str(e))
        
        return user_info
    
    def create_node(self, node_data: Dict[str, Any]) -> Dict[str, Any]:
        """ノード作成"""
        try:
            response = self.supabase.table('nodes').insert(node_data).execute()
            if not response.data:
                raise HTTPException(status_code=500, detail="ノード作成に失敗しました")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            logger.error("ノード作成エラー", error=str(e), node_data=node_data)
            raise HTTPException(status_code=500, detail=f"ノード作成中にエラーが発生しました: {str(e)}")
    
    def update_node(self, node_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """ノード更新"""
        try:
            response = self.supabase.table('nodes').update(update_data).eq('id', node_id).execute()
            if not response.data:
                raise HTTPException(status_code=404, detail="更新対象のノードが見つかりません")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            logger.error("ノード更新エラー", node_id=node_id, error=str(e))
            raise HTTPException(status_code=500, detail=f"ノード更新中にエラーが発生しました: {str(e)}")
    
    def delete_node(self, node_id: str) -> bool:
        """ノード削除（論理削除）"""
        try:
            response = self.supabase.table('nodes').update({
                'deleted_at': datetime.now().isoformat()
            }).eq('id', node_id).execute()
            return bool(response.data)
        except Exception as e:
            logger.error("ノード削除エラー", node_id=node_id, error=str(e))
            raise HTTPException(status_code=500, detail=f"ノード削除中にエラーが発生しました: {str(e)}")
    
    # ===== ブロック管理 =====
    
    def get_node_blocks(self, node_id: str) -> List[Dict[str, Any]]:
        """ノードのブロック一覧取得"""
        response = self.supabase.table('blocks').select('*').eq('node_id', node_id).is_('deleted_at', 'null').order('sort_order').execute()
        return response.data or []
    
    def get_block(self, block_id: str) -> Optional[Dict[str, Any]]:
        """特定のブロック取得"""
        try:
            response = self.supabase.table('blocks').select('*').eq('id', block_id).is_('deleted_at', 'null').single().execute()
            return response.data if response.data else None
        except Exception as e:
            logger.error("ブロック取得エラー", block_id=block_id, error=str(e))
            return None
    
    def update_block(self, block_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """ブロック更新"""
        try:
            response = self.supabase.table('blocks').update(update_data).eq('id', block_id).execute()
            if not response.data:
                raise HTTPException(status_code=404, detail="更新対象のブロックが見つかりません")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            logger.error("ブロック更新エラー", block_id=block_id, error=str(e))
            raise HTTPException(status_code=500, detail=f"ブロック更新中にエラーが発生しました: {str(e)}")
    
    def delete_block(self, block_id: str) -> bool:
        """ブロック削除（論理削除）"""
        try:
            response = self.supabase.table('blocks').update({
                'deleted_at': datetime.now().isoformat()
            }).eq('id', block_id).execute()
            return bool(response.data)
        except Exception as e:
            logger.error("ブロック削除エラー", block_id=block_id, error=str(e))
            raise HTTPException(status_code=500, detail=f"ブロック削除中にエラーが発生しました: {str(e)}")
    
    def reorder_blocks(self, block_ids: List[str], user_id: str) -> bool:
        """ブロック順序変更"""
        try:
            for index, block_id in enumerate(block_ids):
                # 所有者チェック
                if not self.check_block_ownership(block_id, user_id):
                    raise HTTPException(status_code=403, detail=f"ブロック {block_id} を並び替える権限がありません")
                
                # 順序更新
                response = self.supabase.table('blocks').update({
                    'sort_order': index
                }).eq('id', block_id).execute()
                
                if not response.data:
                    raise HTTPException(status_code=500, detail=f"ブロック {block_id} の順序更新に失敗しました")
            
            return True
        except HTTPException:
            raise
        except Exception as e:
            logger.error("ブロック順序変更エラー", block_ids=block_ids, error=str(e))
            raise HTTPException(status_code=500, detail=f"ブロック順序変更中にエラーが発生しました: {str(e)}")
    
    # ===== テーマ関連 =====
    
    def get_theme_blocks_filtered(self, theme_id: str, current_user_id: str) -> List[Dict[str, Any]]:
        """テーマのブロック一覧取得（フィルタリング済み）"""
        logger.info("テーマブロック取得開始", theme_id=theme_id, user_id=current_user_id)
        
        # JOINクエリで一度にブロック、ノード、ユーザー情報を取得
        response = self.supabase.table('blocks').select('''
            id, title, content, updated_at, creator_id, node_id,
            nodes!blocks_node_id_fkey(
                id, title, is_public, user_id,
                users!nodes_user_id_fkey(name)
            )
        ''').eq('block_theme_id', theme_id).is_('deleted_at', 'null').order('updated_at', desc=True).execute()
        
        if not response.data:
            logger.warning("テーマに関連するブロックが見つかりません", theme_id=theme_id)
            return []
        
        filtered_blocks = []
        
        for block in response.data:
            node = block.get('nodes')
            if not node:
                continue
            
            # フィルタリング条件: 公開ノードまたは自分のノード
            is_public = node.get('is_public', False)
            is_own_node = node.get('user_id') == current_user_id
            
            if is_public or is_own_node:
                # ブロックにノード情報を追加
                block['node_title'] = node.get('title')
                if node.get('users'):
                    block['user_name'] = node['users'].get('name')
                
                # 不要なネストしたデータを削除
                del block['nodes']
                filtered_blocks.append(block)
        
        logger.info("テーマブロック取得完了", theme_id=theme_id, count=len(filtered_blocks))
        return filtered_blocks
    
    def get_themes_with_count(self) -> List[Dict[str, Any]]:
        """ブロック数付きテーマ一覧取得"""
        # テーマ一覧を取得
        themes_response = self.supabase.table('block_themes').select('*').order('updated_at', desc=True).execute()
        
        if not themes_response.data:
            return []
        
        # 全テーマのブロック数を一度のクエリで取得
        theme_ids = [theme['id'] for theme in themes_response.data]
        blocks_response = self.supabase.table('blocks').select('block_theme_id').in_('block_theme_id', theme_ids).is_('deleted_at', 'null').execute()
        
        # ブロック数をカウント
        block_counts = {}
        if blocks_response.data:
            for block in blocks_response.data:
                theme_id = block['block_theme_id']
                block_counts[theme_id] = block_counts.get(theme_id, 0) + 1
        
        # テーマにブロック数を追加
        themes_with_count = []
        for theme in themes_response.data:
            theme['block_count'] = block_counts.get(theme['id'], 0)
            themes_with_count.append(theme)
        
        return themes_with_count
    
    # ===== アクティビティ =====
    
    def get_user_activity(self, user_id: str) -> List[Dict[str, Any]]:
        """ユーザーのアクティビティ取得（他のユーザーの活動のみ）"""
        # JOINクエリで一度にブロック、ノード、ユーザー情報を取得
        response = self.supabase.table('blocks').select('''
            id, title, updated_at, user_id, node_id,
            nodes!blocks_node_id_fkey(
                id, title, user_id, deleted_at, is_public
            ),
            users!blocks_user_id_fkey(name)
        ''').neq('user_id', user_id).is_('deleted_at', 'null').order('updated_at', desc=True).limit(50).execute()
        
        if not response.data:
            return []
        
        activities = []
        for block in response.data:
            node = block.get('nodes')
            if not node or node.get('deleted_at'):
                continue
            
            # 公開ノードのみ表示
            if not node.get('is_public', False):
                continue
            
            # ブロック作成者のユーザー情報を取得
            user_name = 'Unknown User'
            if block.get('users') and block['users'].get('name'):
                user_name = block['users']['name']
            
            activity = {
                'block_id': block['id'],
                'block_title': block['title'],
                'block_updated_at': block['updated_at'],
                'node_title': node['title'],
                'user_name': user_name,
                'user_id': block['user_id'],
                'node_id': node['id']
            }
            activities.append(activity)
        
        return activities 