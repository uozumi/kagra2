import React, { useState } from 'react';
import { Box, Container, AppBar, Toolbar, Typography, Button } from '@mui/material';
import SupabaseLoginModal from '../components/SupabaseLoginModal';

interface LandingLayoutProps {
  children: React.ReactNode;
}

const LandingLayout: React.FC<LandingLayoutProps> = ({ children }) => {
  const [loginOpen, setLoginOpen] = useState(false);

  const handleOpenLogin = () => {
    setLoginOpen(true);
  };

  const handleCloseLogin = () => {
    setLoginOpen(false);
  };
  
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar 
        position="fixed" 
        color="transparent" 
        elevation={0}
        sx={{ 
          borderBottom: '1px solid',
          borderColor: 'divider',
          zIndex: 1300
        }}
      >
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            KAGRA
          </Typography>
          <Button 
            variant="contained" 
            color="primary" 
            onClick={handleOpenLogin}
          >
            ログイン
          </Button>
        </Toolbar>
      </AppBar>
      <Box sx={{ height: 64 }} />
      <Container component="main" sx={{ mt: 8, mb: 2, flexGrow: 1 }}>
        {children}
      </Container>
      <Box component="footer" sx={{ py: 3, textAlign: 'center', mt: 'auto', bgcolor: 'background.paper' }}>
        <Typography variant="body2" color="text.secondary">
          © {new Date().getFullYear()} KAGRA
        </Typography>
      </Box>
      <SupabaseLoginModal open={loginOpen} onClose={handleCloseLogin} />
    </Box>
  );
};

export default LandingLayout; 