-- 未設定のRLSポリシーを追加
-- 実行日: 2024年12月

-- 1. block_theme_categories テーブル
-- ユーザー関連カラムが存在しないため、認証状態ベースのポリシーを設定
DROP POLICY IF EXISTS "block_theme_categories_select_policy" ON public.block_theme_categories;
CREATE POLICY "block_theme_categories_select_policy" ON public.block_theme_categories
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "block_theme_categories_insert_policy" ON public.block_theme_categories;
CREATE POLICY "block_theme_categories_insert_policy" ON public.block_theme_categories
    FOR INSERT WITH CHECK (
        auth.role() = ANY(ARRAY['authenticated'::text, 'service_role'::text])
    );

DROP POLICY IF EXISTS "block_theme_categories_update_policy" ON public.block_theme_categories;
CREATE POLICY "block_theme_categories_update_policy" ON public.block_theme_categories
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM user_system_permissions 
            WHERE user_id = auth.uid() AND permission_level = 1
        )
    );

DROP POLICY IF EXISTS "block_theme_categories_delete_policy" ON public.block_theme_categories;
CREATE POLICY "block_theme_categories_delete_policy" ON public.block_theme_categories
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM user_system_permissions 
            WHERE user_id = auth.uid() AND permission_level = 1
        )
    );

-- 2. departments テーブル
-- tenant_idベースでアクセス制御
DROP POLICY IF EXISTS "departments_select_policy" ON public.departments;
CREATE POLICY "departments_select_policy" ON public.departments
    FOR SELECT USING (
        -- システム管理者
        EXISTS (
            SELECT 1 FROM user_system_permissions 
            WHERE user_id = auth.uid() AND permission_level = 1
        )
        OR
        -- 同じテナントのユーザー
        EXISTS (
            SELECT 1 FROM user_tenants ut
            WHERE ut.user_id = auth.uid() AND ut.tenant_id = departments.tenant_id
        )
    );

DROP POLICY IF EXISTS "departments_insert_policy" ON public.departments;
CREATE POLICY "departments_insert_policy" ON public.departments
    FOR INSERT WITH CHECK (
        -- システム管理者
        EXISTS (
            SELECT 1 FROM user_system_permissions 
            WHERE user_id = auth.uid() AND permission_level = 1
        )
        OR
        -- テナント管理者
        EXISTS (
            SELECT 1 FROM user_tenant_permissions utp
            JOIN user_tenants ut ON ut.user_id = utp.user_id AND ut.tenant_id = utp.tenant_id
            WHERE utp.user_id = auth.uid() 
            AND ut.tenant_id = departments.tenant_id 
            AND utp.permission_level = 1
        )
    );

DROP POLICY IF EXISTS "departments_update_policy" ON public.departments;
CREATE POLICY "departments_update_policy" ON public.departments
    FOR UPDATE USING (
        -- システム管理者
        EXISTS (
            SELECT 1 FROM user_system_permissions 
            WHERE user_id = auth.uid() AND permission_level = 1
        )
        OR
        -- テナント管理者
        EXISTS (
            SELECT 1 FROM user_tenant_permissions utp
            JOIN user_tenants ut ON ut.user_id = utp.user_id AND ut.tenant_id = utp.tenant_id
            WHERE utp.user_id = auth.uid() 
            AND ut.tenant_id = departments.tenant_id 
            AND utp.permission_level = 1
        )
    );

DROP POLICY IF EXISTS "departments_delete_policy" ON public.departments;
CREATE POLICY "departments_delete_policy" ON public.departments
    FOR DELETE USING (
        -- システム管理者
        EXISTS (
            SELECT 1 FROM user_system_permissions 
            WHERE user_id = auth.uid() AND permission_level = 1
        )
        OR
        -- テナント管理者
        EXISTS (
            SELECT 1 FROM user_tenant_permissions utp
            JOIN user_tenants ut ON ut.user_id = utp.user_id AND ut.tenant_id = utp.tenant_id
            WHERE utp.user_id = auth.uid() 
            AND ut.tenant_id = departments.tenant_id 
            AND utp.permission_level = 1
        )
    );

-- 3. tenant_groups テーブル（現在未使用）
-- システム管理者のみアクセス可能（将来の使用に備えて厳格に設定）
DROP POLICY IF EXISTS "tenant_groups_select_policy" ON public.tenant_groups;
CREATE POLICY "tenant_groups_select_policy" ON public.tenant_groups
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM user_system_permissions 
            WHERE user_id = auth.uid() AND permission_level = 1
        )
    );

DROP POLICY IF EXISTS "tenant_groups_insert_policy" ON public.tenant_groups;
CREATE POLICY "tenant_groups_insert_policy" ON public.tenant_groups
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM user_system_permissions 
            WHERE user_id = auth.uid() AND permission_level = 1
        )
    );

DROP POLICY IF EXISTS "tenant_groups_update_policy" ON public.tenant_groups;
CREATE POLICY "tenant_groups_update_policy" ON public.tenant_groups
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM user_system_permissions 
            WHERE user_id = auth.uid() AND permission_level = 1
        )
    );

DROP POLICY IF EXISTS "tenant_groups_delete_policy" ON public.tenant_groups;
CREATE POLICY "tenant_groups_delete_policy" ON public.tenant_groups
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM user_system_permissions 
            WHERE user_id = auth.uid() AND permission_level = 1
        )
    );

-- 4. tenant_group_memberships テーブル
-- tenant_idベースでアクセス制御（user_idカラムが存在しないため）
DROP POLICY IF EXISTS "tenant_group_memberships_select_policy" ON public.tenant_group_memberships;
CREATE POLICY "tenant_group_memberships_select_policy" ON public.tenant_group_memberships
    FOR SELECT USING (
        -- システム管理者
        EXISTS (
            SELECT 1 FROM user_system_permissions 
            WHERE user_id = auth.uid() AND permission_level = 1
        )
        OR
        -- 同じテナントのユーザー
        EXISTS (
            SELECT 1 FROM user_tenants ut
            WHERE ut.user_id = auth.uid() AND ut.tenant_id = tenant_group_memberships.tenant_id
        )
    );

DROP POLICY IF EXISTS "tenant_group_memberships_insert_policy" ON public.tenant_group_memberships;
CREATE POLICY "tenant_group_memberships_insert_policy" ON public.tenant_group_memberships
    FOR INSERT WITH CHECK (
        -- システム管理者
        EXISTS (
            SELECT 1 FROM user_system_permissions 
            WHERE user_id = auth.uid() AND permission_level = 1
        )
        OR
        -- テナント管理者
        EXISTS (
            SELECT 1 FROM user_tenant_permissions utp
            JOIN user_tenants ut ON ut.user_id = utp.user_id AND ut.tenant_id = utp.tenant_id
            WHERE utp.user_id = auth.uid() 
            AND ut.tenant_id = tenant_group_memberships.tenant_id 
            AND utp.permission_level = 1
        )
    );

DROP POLICY IF EXISTS "tenant_group_memberships_update_policy" ON public.tenant_group_memberships;
CREATE POLICY "tenant_group_memberships_update_policy" ON public.tenant_group_memberships
    FOR UPDATE USING (
        -- システム管理者
        EXISTS (
            SELECT 1 FROM user_system_permissions 
            WHERE user_id = auth.uid() AND permission_level = 1
        )
        OR
        -- テナント管理者
        EXISTS (
            SELECT 1 FROM user_tenant_permissions utp
            JOIN user_tenants ut ON ut.user_id = utp.user_id AND ut.tenant_id = utp.tenant_id
            WHERE utp.user_id = auth.uid() 
            AND ut.tenant_id = tenant_group_memberships.tenant_id 
            AND utp.permission_level = 1
        )
    );

DROP POLICY IF EXISTS "tenant_group_memberships_delete_policy" ON public.tenant_group_memberships;
CREATE POLICY "tenant_group_memberships_delete_policy" ON public.tenant_group_memberships
    FOR DELETE USING (
        -- システム管理者
        EXISTS (
            SELECT 1 FROM user_system_permissions 
            WHERE user_id = auth.uid() AND permission_level = 1
        )
        OR
        -- テナント管理者
        EXISTS (
            SELECT 1 FROM user_tenant_permissions utp
            JOIN user_tenants ut ON ut.user_id = utp.user_id AND ut.tenant_id = utp.tenant_id
            WHERE utp.user_id = auth.uid() 
            AND ut.tenant_id = tenant_group_memberships.tenant_id 
            AND utp.permission_level = 1
        )
    );

-- 5. trigger_logs テーブル
-- ユーザー関連カラムが存在しないため、管理者のみアクセス可能
DROP POLICY IF EXISTS "trigger_logs_select_policy" ON public.trigger_logs;
CREATE POLICY "trigger_logs_select_policy" ON public.trigger_logs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM user_system_permissions 
            WHERE user_id = auth.uid() AND permission_level = 1
        )
    );

DROP POLICY IF EXISTS "trigger_logs_insert_policy" ON public.trigger_logs;
CREATE POLICY "trigger_logs_insert_policy" ON public.trigger_logs
    FOR INSERT WITH CHECK (
        -- システムまたはサービスロールのみ
        auth.role() = ANY(ARRAY['service_role'::text])
        OR
        EXISTS (
            SELECT 1 FROM user_system_permissions 
            WHERE user_id = auth.uid() AND permission_level = 1
        )
    );

-- trigger_logsは通常更新・削除しない（ログの整合性保持）
DROP POLICY IF EXISTS "trigger_logs_update_policy" ON public.trigger_logs;
CREATE POLICY "trigger_logs_update_policy" ON public.trigger_logs
    FOR UPDATE USING (false); -- 更新禁止

DROP POLICY IF EXISTS "trigger_logs_delete_policy" ON public.trigger_logs;
CREATE POLICY "trigger_logs_delete_policy" ON public.trigger_logs
    FOR DELETE USING (
        -- システム管理者のみ削除可能
        EXISTS (
            SELECT 1 FROM user_system_permissions 
            WHERE user_id = auth.uid() AND permission_level = 1
        )
    );

-- ポリシー設定完了のコメント
COMMENT ON TABLE public.block_theme_categories IS 'RLSポリシー設定済み - 2024年12月';
COMMENT ON TABLE public.departments IS 'RLSポリシー設定済み - 2024年12月';
COMMENT ON TABLE public.tenant_groups IS 'RLSポリシー設定済み（未使用テーブル） - 2024年12月';
COMMENT ON TABLE public.tenant_group_memberships IS 'RLSポリシー設定済み - 2024年12月';
COMMENT ON TABLE public.trigger_logs IS 'RLSポリシー設定済み - 2024年12月'; 