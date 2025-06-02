-- セキュアなRLSポリシーの実装
-- 現在の危険な default_policy を削除し、適切なセキュリティポリシーを設定

-- 1. 危険なdefault_policyを削除
DROP POLICY IF EXISTS "default_policy" ON public.blocks;
DROP POLICY IF EXISTS "default_policy" ON public.nodes;
DROP POLICY IF EXISTS "default_policy" ON public.themes;
DROP POLICY IF EXISTS "default_policy" ON public.users;
DROP POLICY IF EXISTS "default_policy" ON public.tenant_users;
DROP POLICY IF EXISTS "default_policy" ON public.tenant_groups;
DROP POLICY IF EXISTS "default_policy" ON public.tenant_group_memberships;
DROP POLICY IF EXISTS "default_policy" ON public.departments;
DROP POLICY IF EXISTS "default_policy" ON public.department_users;
DROP POLICY IF EXISTS "default_policy" ON public.resources;

-- 2. RLSを有効化（既に有効な場合はスキップされる）
ALTER TABLE public.blocks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.themes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tenant_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tenant_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tenant_group_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.departments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.department_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.resources ENABLE ROW LEVEL SECURITY;

-- 3. 監査ログテーブルを作成（存在しない場合）
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    action TEXT NOT NULL,
    user_id UUID REFERENCES auth.users(id),
    user_email TEXT,
    resource_type TEXT,
    resource_id TEXT,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    level TEXT DEFAULT 'info',
    success BOOLEAN DEFAULT true,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 監査ログテーブルのRLS設定（管理者のみアクセス可能）
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- 4. セキュアなポリシーを設定

-- ===== USERSテーブル =====
-- ユーザーは自分の情報のみ閲覧・更新可能
CREATE POLICY "users_select_own" ON public.users
    FOR SELECT USING (
        auth.uid() = auth_id OR 
        auth.uid() = id::uuid
    );

CREATE POLICY "users_update_own" ON public.users
    FOR UPDATE USING (
        auth.uid() = auth_id OR 
        auth.uid() = id::uuid
    );

-- 新規ユーザー作成は認証済みユーザーのみ
CREATE POLICY "users_insert_authenticated" ON public.users
    FOR INSERT WITH CHECK (
        auth.role() = 'authenticated'
    );

-- ===== NODESテーブル =====
-- ノードの閲覧：所有者または公開ノード
CREATE POLICY "nodes_select_policy" ON public.nodes
    FOR SELECT USING (
        user_id = auth.uid() OR 
        is_public = true
    );

-- ノードの作成：認証済みユーザーが自分のノードとして作成
CREATE POLICY "nodes_insert_policy" ON public.nodes
    FOR INSERT WITH CHECK (
        user_id = auth.uid() AND
        auth.role() = 'authenticated'
    );

-- ノードの更新：所有者のみ
CREATE POLICY "nodes_update_policy" ON public.nodes
    FOR UPDATE USING (
        user_id = auth.uid()
    );

-- ノードの削除：所有者のみ
CREATE POLICY "nodes_delete_policy" ON public.nodes
    FOR DELETE USING (
        user_id = auth.uid()
    );

-- ===== BLOCKSテーブル =====
-- ブロックの閲覧：ノードの所有者または公開ノードのブロック
CREATE POLICY "blocks_select_policy" ON public.blocks
    FOR SELECT USING (
        user_id = auth.uid() OR 
        EXISTS (
            SELECT 1 FROM public.nodes 
            WHERE nodes.id = blocks.node_id 
            AND (nodes.user_id = auth.uid() OR nodes.is_public = true)
        )
    );

-- ブロックの作成：認証済みユーザーが自分のノードに作成
CREATE POLICY "blocks_insert_policy" ON public.blocks
    FOR INSERT WITH CHECK (
        user_id = auth.uid() AND
        auth.role() = 'authenticated' AND
        EXISTS (
            SELECT 1 FROM public.nodes 
            WHERE nodes.id = blocks.node_id 
            AND nodes.user_id = auth.uid()
        )
    );

-- ブロックの更新：所有者のみ
CREATE POLICY "blocks_update_policy" ON public.blocks
    FOR UPDATE USING (
        user_id = auth.uid()
    );

-- ブロックの削除：所有者のみ
CREATE POLICY "blocks_delete_policy" ON public.blocks
    FOR DELETE USING (
        user_id = auth.uid()
    );

-- ===== THEMESテーブル =====
-- テーマの閲覧：所有者または公開テーマ
CREATE POLICY "themes_select_policy" ON public.themes
    FOR SELECT USING (
        user_id = auth.uid() OR 
        is_public = true
    );

-- テーマの作成：認証済みユーザーのみ
CREATE POLICY "themes_insert_policy" ON public.themes
    FOR INSERT WITH CHECK (
        user_id = auth.uid() AND
        auth.role() = 'authenticated'
    );

-- テーマの更新：所有者のみ
CREATE POLICY "themes_update_policy" ON public.themes
    FOR UPDATE USING (
        user_id = auth.uid()
    );

-- テーマの削除：所有者のみ
CREATE POLICY "themes_delete_policy" ON public.themes
    FOR DELETE USING (
        user_id = auth.uid()
    );

-- ===== TENANT_USERSテーブル =====
-- テナントユーザーの閲覧：同じテナントのメンバーのみ
CREATE POLICY "tenant_users_select_policy" ON public.tenant_users
    FOR SELECT USING (
        user_id = auth.uid() OR
        EXISTS (
            SELECT 1 FROM public.tenant_users tu2
            WHERE tu2.tenant_id = tenant_users.tenant_id
            AND tu2.user_id = auth.uid()
        )
    );

-- テナントユーザーの追加：テナント管理者のみ
CREATE POLICY "tenant_users_insert_policy" ON public.tenant_users
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.tenant_users tu
            WHERE tu.tenant_id = tenant_users.tenant_id
            AND tu.user_id = auth.uid()
            AND tu.role IN ('admin', 'owner')
        )
    );

-- テナントユーザーの更新：テナント管理者のみ
CREATE POLICY "tenant_users_update_policy" ON public.tenant_users
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM public.tenant_users tu
            WHERE tu.tenant_id = tenant_users.tenant_id
            AND tu.user_id = auth.uid()
            AND tu.role IN ('admin', 'owner')
        )
    );

-- テナントユーザーの削除：テナント管理者のみ
CREATE POLICY "tenant_users_delete_policy" ON public.tenant_users
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM public.tenant_users tu
            WHERE tu.tenant_id = tenant_users.tenant_id
            AND tu.user_id = auth.uid()
            AND tu.role IN ('admin', 'owner')
        )
    );

-- ===== AUDIT_LOGSテーブル =====
-- 監査ログの閲覧：システム管理者のみ
CREATE POLICY "audit_logs_select_admin_only" ON public.audit_logs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.users u
            WHERE u.auth_id = auth.uid()
            AND u.role = 'super_admin'
        )
    );

-- 監査ログの作成：サービスロールのみ
CREATE POLICY "audit_logs_insert_service_only" ON public.audit_logs
    FOR INSERT WITH CHECK (
        auth.role() = 'service_role'
    );

-- 監査ログの更新・削除は禁止（不変性を保証）
-- 更新・削除ポリシーは作成しない

-- ===== その他のテーブル =====
-- TENANT_GROUPS: テナントメンバーのみ閲覧可能
CREATE POLICY "tenant_groups_select_policy" ON public.tenant_groups
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.tenant_users tu
            WHERE tu.tenant_id = tenant_groups.tenant_id
            AND tu.user_id = auth.uid()
        )
    );

-- DEPARTMENTS: 同じテナントのメンバーのみ
CREATE POLICY "departments_select_policy" ON public.departments
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.tenant_users tu
            WHERE tu.tenant_id = departments.tenant_id
            AND tu.user_id = auth.uid()
        )
    );

-- RESOURCES: 所有者または公開リソース
CREATE POLICY "resources_select_policy" ON public.resources
    FOR SELECT USING (
        user_id = auth.uid() OR 
        is_public = true
    );

-- 5. サービスロール用のバイパスポリシー（FastAPI用）
-- service_roleは全てのテーブルにアクセス可能
CREATE POLICY "service_role_bypass" ON public.blocks
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "service_role_bypass" ON public.nodes
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "service_role_bypass" ON public.themes
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "service_role_bypass" ON public.users
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "service_role_bypass" ON public.tenant_users
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "service_role_bypass" ON public.tenant_groups
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "service_role_bypass" ON public.tenant_group_memberships
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "service_role_bypass" ON public.departments
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "service_role_bypass" ON public.department_users
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "service_role_bypass" ON public.resources
    FOR ALL USING (auth.role() = 'service_role');

-- 6. インデックスの最適化
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON public.audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON public.audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON public.audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON public.audit_logs(resource_type, resource_id);

-- 7. コメント追加
COMMENT ON TABLE public.audit_logs IS '監査ログテーブル - システムの全操作を記録';
COMMENT ON POLICY "service_role_bypass" ON public.blocks IS 'FastAPI（service_role）用のバイパスポリシー';
COMMENT ON POLICY "blocks_select_policy" ON public.blocks IS 'ブロック閲覧：所有者または公開ノードのブロック';
COMMENT ON POLICY "nodes_select_policy" ON public.nodes IS 'ノード閲覧：所有者または公開ノード'; 