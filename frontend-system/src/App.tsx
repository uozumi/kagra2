import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { 
  CssBaseline, 
  Container, 
  AppBar, 
  Toolbar, 
  Typography, 
  Button, 
  Box, 
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  IconButton,
  useMediaQuery,
  useTheme
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  People as PeopleIcon,
  ExitToApp as ExitToAppIcon
} from '@mui/icons-material';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import SupabaseLoginModal from './components/SupabaseLoginModal';
import Dashboard from './pages/Dashboard';
import Members from './pages/Members';
import './App.css';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

const drawerWidth = 240;

// 認証が必要なルートのラッパー
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading, isSystemAdmin } = useAuth();

  // デバッグログ
  console.log('🛡️ ProtectedRoute状態:', {
    loading,
    hasUser: !!user,
    isSystemAdmin,
    userId: user?.id
  });

  if (loading) {
    console.log('⏳ ProtectedRoute: ローディング中...');
    return (
      <Container maxWidth="md" sx={{ mt: 4, textAlign: 'center' }}>
        <Typography variant="h6">読み込み中...</Typography>
      </Container>
    );
  }

  if (!user) {
    console.log('🚫 ProtectedRoute: ユーザーなし - ログインページにリダイレクト');
    return <Navigate to="/login" replace />;
  }

  if (!isSystemAdmin) {
    console.log('🚫 ProtectedRoute: システム管理者権限なし');
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Typography variant="h4" color="error">
          アクセス権限がありません
        </Typography>
        <Typography variant="body1" sx={{ mt: 2 }}>
          このページにアクセスするにはシステム管理者権限が必要です。
        </Typography>
        <Typography variant="body2" sx={{ mt: 1, color: 'text.secondary' }}>
          user_permissions_viewでis_system_admin=TRUEかつpermission_level=1の権限が必要です。
        </Typography>
      </Container>
    );
  }

  console.log('✅ ProtectedRoute: アクセス許可');
  return <>{children}</>;
};

// サイドバーコンポーネント
const Sidebar: React.FC<{ open: boolean; onClose: () => void; variant: 'temporary' | 'permanent' }> = ({ 
  open, 
  onClose, 
  variant 
}) => {
  const location = useLocation();
  const { user, signOut } = useAuth();

  const handleSignOut = async () => {
    await signOut();
  };

  const menuItems = [
    { text: 'ダッシュボード', icon: <DashboardIcon />, path: '/' },
    { text: 'メンバー管理', icon: <PeopleIcon />, path: '/members' },
  ];

  const drawer = (
    <Box>
      <Toolbar>
        <Typography variant="h6" noWrap component="div">
          システム管理
        </Typography>
      </Toolbar>
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              component={Link}
              to={item.path}
              selected={location.pathname === item.path}
              onClick={variant === 'temporary' ? onClose : undefined}
            >
              <ListItemIcon>
                {item.icon}
              </ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      {user && (
        <Box sx={{ position: 'absolute', bottom: 0, width: '100%', p: 2 }}>
          <Typography variant="body2" sx={{ mb: 1, wordBreak: 'break-word' }}>
            {user.email}
          </Typography>
          <Button
            fullWidth
            variant="outlined"
            startIcon={<ExitToAppIcon />}
            onClick={handleSignOut}
            size="small"
          >
            ログアウト
          </Button>
        </Box>
      )}
    </Box>
  );

  return (
    <Drawer
      variant={variant}
      open={open}
      onClose={onClose}
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
        },
      }}
    >
      {drawer}
    </Drawer>
  );
};

// ナビゲーションバー
const NavigationBar: React.FC<{ onMenuClick: () => void }> = ({ onMenuClick }) => {
  const { user } = useAuth();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  return (
    <AppBar 
      position="fixed" 
      sx={{ 
        zIndex: (theme) => theme.zIndex.drawer + 1,
        ...(isMobile ? {} : { ml: `${drawerWidth}px`, width: `calc(100% - ${drawerWidth}px)` })
      }}
    >
      <Toolbar>
        {isMobile && (
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={onMenuClick}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
        )}
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          システム管理画面
        </Typography>
        {user && !isMobile && (
          <Typography variant="body2">
            {user.email}
          </Typography>
        )}
      </Toolbar>
    </AppBar>
  );
};

// ログインページ
const LoginPage: React.FC = () => {
  const [loginModalOpen, setLoginModalOpen] = useState(true);

  console.log('🔑 LoginPage表示');

  const handleCloseLoginModal = () => {
    console.log('🔑 LoginModal閉じる');
    setLoginModalOpen(false);
  };

  const handleOpenLoginModal = () => {
    console.log('🔑 LoginModal開く');
    setLoginModalOpen(true);
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 8 }}>
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          システム管理画面
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          システム管理者権限でログインしてください
        </Typography>
        
        {!loginModalOpen && (
          <Button 
            variant="contained" 
            size="large" 
            onClick={handleOpenLoginModal}
            sx={{ mt: 2 }}
          >
            ログイン
          </Button>
        )}
      </Box>
      
      <SupabaseLoginModal
        open={loginModalOpen}
        onClose={handleCloseLoginModal}
        title="システム管理者ログイン"
      />
    </Container>
  );
};

// メインレイアウト
const MainLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  return (
    <Box sx={{ display: 'flex' }}>
      <NavigationBar onMenuClick={handleDrawerToggle} />
      
      {/* モバイル用サイドバー */}
      {isMobile && (
        <Sidebar
          open={mobileOpen}
          onClose={handleDrawerToggle}
          variant="temporary"
        />
      )}
      
      {/* デスクトップ用サイドバー */}
      {!isMobile && (
        <Sidebar
          open={true}
          onClose={() => {}}
          variant="permanent"
        />
      )}
      
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { md: `calc(100% - ${drawerWidth}px)` },
          mt: '64px', // AppBarの高さ分
        }}
      >
        {children}
      </Box>
    </Box>
  );
};

// アプリケーションコンテンツ
const AppContent: React.FC = () => {
  const { user } = useAuth();

  console.log('🏠 AppContent表示:', {
    hasUser: !!user,
    userId: user?.id
  });

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <MainLayout>
              <Dashboard />
            </MainLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/members"
        element={
          <ProtectedRoute>
            <MainLayout>
              <Members />
            </MainLayout>
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Router>
          <AppContent />
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
