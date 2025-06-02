from typing import List, Optional, Dict, Any, Union
from fastapi import HTTPException
from app.models.user import User
from app.models.charaxy import Node, Block, BlockTheme, ActivityItem
import structlog

logger = structlog.get_logger()

class CharaxyService:
    def __init__(self, supabase) -> None:
        self.supabase = supabase
    
    # 権限チェック共通処理
    def _check_ownership(self, table_name: str, resource_id: str, user_id: str, user_field: str = 'user_id') -> bool:
        """リソースの所有者チェック（共通処理）"""
        try:
            response = self.supabase.table(table_name).select(user_field).eq('id', resource_id)
            
            # 論理削除対応（deleted_atがあるテーブルのみ）
            if table_name in ['nodes', 'blocks']:
                response = response.is_('deleted_at', 'null')
            
            result = response.single().execute()
            return result.data and result.data[user_field] == user_id
        except Exception as e:
            logger.error("所有者チェックエラー", table=table_name, resource_id=resource_id, error=str(e))
            return False
    
    def check_node_ownership(self, node_id: str, user_id: str) -> bool:
        """ノードの所有者チェック"""
        return self._check_ownership('nodes', node_id, user_id)
    
    def check_block_ownership(self, block_id: str, user_id: str) -> bool:
        """ブロックの所有者チェック"""
        return self._check_ownership('blocks', block_id, user_id)
    
    def check_theme_ownership(self, theme_id: str, user_id: str) -> bool:
        """テーマの所有者チェック"""
        return self._check_ownership('block_themes', theme_id, user_id, 'creator_id')
    
    # ユーザー情報取得共通処理
    def get_user_with_affiliations(self, user_id: str) -> Optional[Dict[str, Any]]:
        """ユーザー情報と所属情報を取得"""
        try:
            # 1. ユーザー基本情報を取得
            users_response = self.supabase.table('users').select('id, name, avatar_url').eq('id', user_id).execute()
            
            if not users_response.data:
                return None
            
            user_data = users_response.data[0]
            
            # 2. プロファイル情報を取得（アバターのフォールバック）
            avatar_url = user_data.get('avatar_url')
            if not avatar_url:
                profiles_response = self.supabase.table('user_profiles').select('avatar_url').eq('user_id', user_id).execute()
                if profiles_response.data and profiles_response.data[0].get('avatar_url'):
                    avatar_url = profiles_response.data[0]['avatar_url']
            
            # 3. 所属情報を取得
            affiliations = self._get_user_affiliations(user_id)
            
            return {
                'id': user_data['id'],
                'name': user_data.get('name', ''),
                'avatar_url': avatar_url,
                'affiliations': affiliations
            }
            
        except Exception as e:
            logger.error(f"[ERROR] ユーザー情報取得エラー: {str(e)}")
            return None
    
    def _get_user_affiliations(self, user_id: str) -> List[Dict[str, Any]]:
        """ユーザーの所属情報を取得（内部メソッド）"""
        try:
            affiliations = []
            
            # user_tenantsからテナント情報を取得
            user_tenants_response = self.supabase.table('user_tenants').select(
                'tenant_id, role, tenants!inner(id, name)'
            ).eq('user_id', user_id).execute()
            
            # user_departmentsから部署情報を取得
            user_departments_response = self.supabase.table('user_departments').select(
                'tenant_id, department_id, position, departments!inner(id, name)'
            ).eq('user_id', user_id).execute()
            
            # tenantIdごとにグループ化
            tenant_map = {}
            
            # テナント情報を処理
            for ut in user_tenants_response.data or []:
                tenant_id = ut['tenant_id']
                tenant_name = ut['tenants']['name'] if ut.get('tenants') else '不明なテナント'
                
                if tenant_id not in tenant_map:
                    tenant_map[tenant_id] = {'tenantName': tenant_name, 'departments': []}
            
            # 部署情報を処理
            for ud in user_departments_response.data or []:
                tenant_id = ud['tenant_id']
                dept_name = ud['departments']['name'] if ud.get('departments') else None
                
                if tenant_id in tenant_map and dept_name and dept_name not in tenant_map[tenant_id]['departments']:
                    tenant_map[tenant_id]['departments'].append(dept_name)
            
            # 結果を配列に変換
            for tenant_id, info in tenant_map.items():
                affiliations.append({
                    'tenantId': tenant_id,
                    'tenantName': info['tenantName'],
                    'departments': info['departments']
                })
            
            return affiliations
            
        except Exception as e:
            logger.error(f"[ERROR] 所属情報取得エラー: {str(e)}")
            return []

    # ノード関連処理
    def get_user_nodes(self, user_id: str) -> List[dict]:
        """ユーザーのノード一覧取得"""
        response = self.supabase.table('nodes').select('*').eq('user_id', user_id).eq('type', 'charaxy').is_('deleted_at', 'null').order('updated_at', desc=True).execute()
        return response.data or []
    
    def get_nodes_filtered(self, user_id: str, skip: int = 0, limit: int = 100) -> List[dict]:
        """フィルタリングされたノード一覧取得"""
        try:
            # 公開ノードまたは自分のノードを取得
            response = self.supabase.table('nodes').select('*').or_(
                f'is_public.eq.true,user_id.eq.{user_id}'
            ).eq('type', 'charaxy').is_('deleted_at', 'null').order('updated_at', desc=True).range(skip, skip + limit - 1).execute()
            
            return response.data or []
        except Exception as e:
            logger.error(f"[ERROR] ノード一覧取得エラー: {str(e)}")
            return []
    
    def get_node_by_id(self, node_id: str) -> Optional[dict]:
        """IDによるノード取得"""
        try:
            response = self.supabase.table('nodes').select('*').eq('id', node_id).is_('deleted_at', 'null').single().execute()
            return response.data if response.data else None
        except Exception as e:
            logger.error(f"[ERROR] ノード取得エラー: {str(e)}")
            return None
    
    def get_node_with_user_info(self, node_id: str) -> Optional[dict]:
        """ユーザー情報付きノード取得"""
        try:
            response = self.supabase.table('nodes').select('''
                *,
                users!nodes_user_id_fkey(name, avatar_url)
            ''').eq('id', node_id).is_('deleted_at', 'null').single().execute()
            
            if not response.data:
                return None
            
            node_data = response.data
            
            # ユーザー情報を処理
            if node_data.get('users'):
                user_info = node_data['users']
                node_data['user_name'] = user_info.get('name')
                node_data['user_avatar'] = user_info.get('avatar_url')
                del node_data['users']
                
                # 所属情報も取得
                if node_data.get('user_id'):
                    affiliations = self._get_user_affiliations(node_data['user_id'])
                    node_data['user_affiliations'] = affiliations
            
            return node_data
            
        except Exception as e:
            logger.error(f"[ERROR] ユーザー情報付きノード取得エラー: {str(e)}")
            return None
    
    def create_node(self, node_data: dict) -> dict:
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
    
    def update_node(self, node_id: str, update_data: dict) -> dict:
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
            from datetime import datetime
            response = self.supabase.table('nodes').update({
                'deleted_at': datetime.now().isoformat()
            }).eq('id', node_id).execute()
            return bool(response.data)
        except Exception as e:
            logger.error("ノード削除エラー", node_id=node_id, error=str(e))
            raise HTTPException(status_code=500, detail=f"ノード削除中にエラーが発生しました: {str(e)}")
    
    # ブロック関連処理
    def get_node_blocks(self, node_id: str) -> List[dict]:
        """ノードのブロック一覧取得"""
        response = self.supabase.table('blocks').select('*').eq('node_id', node_id).is_('deleted_at', 'null').order('sort_order').execute()
        return response.data or []
    
    def get_block(self, block_id: str) -> Optional[dict]:
        """特定のブロック取得"""
        response = self.supabase.table('blocks').select('*').eq('id', block_id).is_('deleted_at', 'null').single().execute()
        return response.data if response.data else None
    
    def get_theme_blocks_filtered(self, theme_id: str, current_user_id: str) -> List[dict]:
        """テーマのブロック一覧取得（フィルタリング済み）"""
        # ブロック単体を取得
        blocks_response = self.supabase.table('blocks').select('*').eq('block_theme_id', theme_id).is_('deleted_at', 'null').order('updated_at', desc=True).execute()
        
        if not blocks_response.data:
            return []
        
        filtered_blocks = []
        
        for block in blocks_response.data:
            # ノード情報を取得
            node_response = self.supabase.table('nodes').select('''
                id, title, is_public, user_id, deleted_at,
                users!nodes_user_id_fkey(name)
            ''').eq('id', block['node_id']).single().execute()
            
            if not node_response.data or node_response.data.get('deleted_at'):
                continue
            
            node = node_response.data
            
            # フィルタリング条件: 公開ノードまたは自分のノード
            if node.get('is_public') or node.get('user_id') == current_user_id:
                # ブロックにノード情報を追加
                block['node_title'] = node.get('title')
                if node.get('users'):
                    block['user_name'] = node['users'].get('name')
                
                filtered_blocks.append(block)
        
        return filtered_blocks
    
    # テーマ関連処理
    def get_themes_with_count(self) -> List[dict]:
        """ブロック数付きテーマ一覧取得"""
        themes_response = self.supabase.table('block_themes').select('*').order('updated_at', desc=True).execute()
        
        if not themes_response.data:
            return []
        
        themes_with_count = []
        for theme in themes_response.data:
            # ブロック数を取得
            blocks_response = self.supabase.table('blocks').select('id').eq('block_theme_id', theme['id']).is_('deleted_at', 'null').execute()
            theme['block_count'] = len(blocks_response.data) if blocks_response.data else 0
            themes_with_count.append(theme)
        
        return themes_with_count
    
    # アクティビティ関連処理
    def get_user_activity(self, user_id: str) -> List[dict]:
        """ユーザーのアクティビティ取得（他のユーザーの活動のみ）"""
        # 自分以外のユーザーのブロックを取得
        blocks_response = self.supabase.table('blocks').select('*').neq('user_id', user_id).is_('deleted_at', 'null').order('updated_at', desc=True).limit(50).execute()
        
        logger.debug(f"[DEBUG] アクティビティ取得 - 現在のユーザーID: {user_id}")
        logger.debug(f"[DEBUG] 取得したブロック数: {len(blocks_response.data) if blocks_response.data else 0}")
        
        if not blocks_response.data:
            return []
        
        activities = []
        for block in blocks_response.data:
            logger.debug(f"[DEBUG] ブロック処理中: {block['id']}, ノードID: {block['node_id']}, ブロック作成者: {block['user_id']}")
            
            # ノード情報を取得
            node_response = self.supabase.table('nodes').select('id, title, user_id, deleted_at, is_public').eq('id', block['node_id']).single().execute()
            
            logger.debug(f"[DEBUG] ノード情報: {node_response.data}")
            
            if not node_response.data or node_response.data.get('deleted_at'):
                logger.debug(f"[DEBUG] ノードが見つからないか削除済み: {block['node_id']}")
                continue
            
            node = node_response.data
            
            # 公開ノードのみ表示（プライベートノードは除外）
            if not node.get('is_public', False):
                logger.debug(f"[DEBUG] プライベートノードのため除外: {node['id']}")
                continue
            
            # ユーザー情報を別途取得
            user_name = 'Unknown User'
            try:
                user_response = self.supabase.table('users').select('name').eq('id', node['user_id']).single().execute()
                if user_response.data and user_response.data.get('name'):
                    user_name = user_response.data['name']
                    logger.debug(f"[DEBUG] ユーザー名取得成功: {user_name}")
                else:
                    logger.debug(f"[DEBUG] ユーザー情報が見つかりません - ユーザーID: {node['user_id']}")
            except Exception as e:
                logger.debug(f"[DEBUG] ユーザー情報取得エラー: {str(e)}")
            
            activity = {
                'block_id': block['id'],
                'block_title': block['title'],
                'block_updated_at': block['updated_at'],
                'node_title': node['title'],
                'user_name': user_name,
                'user_id': node['user_id'],
                'node_id': node['id']
            }
            activities.append(activity)
        
        logger.debug(f"[DEBUG] 最終的なアクティビティ数: {len(activities)}")
        return activities 