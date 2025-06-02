import React, { useState, useEffect } from 'react';
import { AppBar, Toolbar, Typography, Button, Box, Menu, MenuItem, CircularProgress, Divider, IconButton, Avatar } from '@mui/material';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import SupabaseLoginModal from './SupabaseLoginModal';
import { supabase } from '../lib/supabase';
import ArrowDropDownIcon from '@mui/icons-material/ArrowDropDown';

interface HeaderProps {
  isAdmin?: boolean;
  isTenantAdmin?: boolean;
}

interface Tenant {
  id: string;
  name: string;
  description?: string;
}

const Header: React.FC<HeaderProps> = ({ isAdmin = false, isTenantAdmin = false }) => {
  const { user, signOut, isSystemAdmin, isAdmin: isAuthAdmin } = useAuth();
  const navigate = useNavigate();
  const [loginOpen, setLoginOpen] = useState(false);
  const [tenantMenuAnchor, setTenantMenuAnchor] = useState<null | HTMLElement>(null);
  const [managedTenants, setManagedTenants] = useState<Tenant[]>([]);
  const [loadingTenants, setLoadingTenants] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null);
  const [avatarError, setAvatarError] = useState(false);
  const open = Boolean(anchorEl);

  // デバッグ用ログ
  useEffect(() => {
    if (user) {
      console.log('Header - 権限状態:', {
        userId: user.id,
        isSystemAdmin,
        isAuthAdmin,
        hasUser: !!user
      });
    }
  }, [user, isSystemAdmin, isAuthAdmin]);

  // ユーザー情報（アバター含む）を取得
  useEffect(() => {
    const fetchUserInfo = async () => {
      if (!user) {
        setAvatarUrl(null);
        return;
      }
      
      try {
        // Supabaseセッションからアクセストークンを取得
        const { data: { session } } = await supabase.auth.getSession();
        
        // FastAPI経由で現在のユーザー情報を取得
        const response = await fetch('/api/v1/users/me', {
          headers: {
            'Authorization': `Bearer ${session?.access_token || ''}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (!response.ok) {
          console.error('ユーザー情報取得エラー:', response.status);
          setAvatarUrl(null);
          return;
        }
        
        const userData = await response.json();
        console.log('Header - ユーザー情報取得成功:', userData);
        
        if (userData.avatar_url) {
          // Google画像の場合はサイズパラメータを調整
          let processedAvatarUrl = userData.avatar_url;
          if (processedAvatarUrl.includes('googleusercontent.com')) {
            processedAvatarUrl = processedAvatarUrl.replace(/=s\d+-c$/, '=s40-c');
          }
          setAvatarUrl(processedAvatarUrl);
          setAvatarError(false);
        } else {
          setAvatarUrl(null);
        }
        
      } catch (err) {
        console.error('Header - ユーザー情報取得エラー:', err);
        setAvatarUrl(null);
      }
    };
    
    fetchUserInfo();
  }, [user]);

  // テナント管理者権限がある場合のテナント情報取得
  useEffect(() => {
    const fetchManagedTenants = async () => {
      if (!user || !isAuthAdmin) {
        setManagedTenants([]);
        return;
      }

      try {
        // Supabaseセッションからアクセストークンを取得
        const { data: { session } } = await supabase.auth.getSession();
        
        // FastAPI経由でユーザーの権限情報を取得
        setLoadingTenants(true);
        const response = await fetch('/api/v1/users/me/permissions', {
          headers: {
            'Authorization': `Bearer ${session?.access_token || ''}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (!response.ok) {
          throw new Error(`権限情報取得エラー: ${response.status}`);
        }
        
        const permissionData = await response.json();
        
        // 管理者権限（permission_level: 1）を持つテナントを抽出
        const adminTenants = permissionData.permissions
          .filter((perm: any) => perm.permission === 1)
          .map((perm: any) => ({
            id: perm.tenant_id,
            name: perm.tenant_name
          }));
        
        setManagedTenants(adminTenants);
        
      } catch (err) {
        console.error('管理テナント取得エラー:', err);
        setManagedTenants([]);
      } finally {
        setLoadingTenants(false);
      }
    };
    
    fetchManagedTenants();
  }, [user, isAuthAdmin]);

  const handleOpenLogin = () => {
    setLoginOpen(true);
  };

  const handleCloseLogin = () => {
    setLoginOpen(false);
  };

  const handleSignOut = async () => {
    await signOut();
  };

  const handleOpenTenantMenu = (event: React.MouseEvent<HTMLElement>) => {
    setTenantMenuAnchor(event.currentTarget);
  };

  const handleCloseTenantMenu = () => {
    setTenantMenuAnchor(null);
  };

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleAccount = () => {
    navigate('/account');
    handleClose();
  };

  return (
    <>
      <AppBar 
        position="fixed" 
        color={isAdmin ? "secondary" : isTenantAdmin ? "primary" : "default"} 
        elevation={0}
        sx={{ 
          borderBottom: '1px solid',
          borderColor: 'divider',
          zIndex: 1300
        }}
      >
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            {isAdmin ? "KAGRA（管理者システム）" : isTenantAdmin ? "KAGRA（テナント管理）" : "KAGRA"}
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 2 }}>
            {user ? (
              <>
                {/* システム管理者メニュー */}
                {isSystemAdmin && (
                  <Button 
                    color="inherit" 
                    component={RouterLink} 
                    to="/admin-system/dashboard"
                    sx={{ fontWeight: isAdmin ? 'bold' : 'normal' }}
                  >
                    システム管理画面
                  </Button>
                )}
                
                {/* テナント管理者メニュー */}
                {isAuthAdmin && (
                  <>
                    <Button 
                      color="inherit"
                      onClick={handleOpenTenantMenu}
                      endIcon={<ArrowDropDownIcon />}
                      sx={{ fontWeight: isTenantAdmin ? 'bold' : 'normal' }}
                    >
                      テナント管理画面
                    </Button>
                    <Menu
                      anchorEl={tenantMenuAnchor}
                      open={Boolean(tenantMenuAnchor)}
                      onClose={handleCloseTenantMenu}
                    >
                      {loadingTenants ? (
                        <MenuItem>
                          <CircularProgress size={20} sx={{ mr: 1 }} />
                          読み込み中...
                        </MenuItem>
                      ) : managedTenants.length > 0 ? (
                        managedTenants.map(tenant => (
                          <MenuItem 
                            key={tenant.id}
                            component={RouterLink} 
                            to={`/admin-tenant/${tenant.id}/dashboard`}
                            onClick={handleCloseTenantMenu}
                          >
                            {tenant.name}
                          </MenuItem>
                        ))
                      ) : (
                        <MenuItem disabled>
                          管理テナントがありません
                        </MenuItem>
                      )}
                    </Menu>
                  </>
                )}
                <Button 
                  color="inherit" 
                  component={RouterLink} 
                  to="/dashboard"
                >
                  ダッシュボード
                </Button>                
                <Box>
                  <IconButton
                    onClick={handleMenu}
                    size="small"
                    sx={{ ml: 2 }}
                    aria-controls={open ? 'account-menu' : undefined}
                    aria-haspopup="true"
                    aria-expanded={open ? 'true' : undefined}
                  >
                    {avatarUrl && !avatarError ? (
                      <Avatar 
                        src={avatarUrl}
                        sx={{ width: 40, height: 40 }}
                        imgProps={{
                          referrerPolicy: 'no-referrer',
                          onLoad: () => {
                            console.log('Header - アバター画像読み込み成功:', avatarUrl);
                          },
                          onError: (e) => {
                            console.error('Header - アバター画像読み込みエラー:', avatarUrl);
                            setAvatarError(true);
                          }
                        }}
                      >
                        {user.email?.charAt(0).toUpperCase()}
                      </Avatar>
                    ) : (
                      <Avatar sx={{ width: 40, height: 40 }}>
                        {user.email?.charAt(0).toUpperCase()}
                      </Avatar>
                    )}
                  </IconButton>
                  <Menu
                    id="account-menu"
                    anchorEl={anchorEl}
                    open={open}
                    onClose={handleClose}
                    transformOrigin={{ horizontal: 'right', vertical: 'top' }}
                    anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
                  >
                    <MenuItem onClick={handleAccount}>
                      アカウント
                    </MenuItem>
                    <MenuItem onClick={handleSignOut}>
                      ログアウト
                    </MenuItem>
                  </Menu>
                </Box>
              </>
            ) : (
              <Button color="inherit" onClick={handleOpenLogin}>
                ログイン
              </Button>
            )}
          </Box>
        </Toolbar>
      </AppBar>
      
      <SupabaseLoginModal open={loginOpen} onClose={handleCloseLogin} />
    </>
  );
};

export default Header; 