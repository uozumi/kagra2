import React from 'react';
import { Box, Container } from '@mui/material';
import Header from '../components/Header';
import DefaultSidebar from '../components/sidebar/Default';

interface DefaultLayoutProps {
  children: React.ReactNode;
  showSidebar?: boolean;
}

const DefaultLayout: React.FC<DefaultLayoutProps> = ({ children, showSidebar = true }) => {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Header />
      <Box sx={{ height: 64 }} />
      <Box sx={{ display: 'flex', flexGrow: 1 }}>
        {showSidebar && <DefaultSidebar />}
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            p: 3,
            width: { sm: showSidebar ? `calc(100% - 240px)` : '100%' }
          }}
        >
          <Container 
            maxWidth="lg" 
            sx={{ 
              ml: 0,
              mr: 'auto',
              px: 0
            }}
          >
            {children}
          </Container>
        </Box>
      </Box>
    </Box>
  );
};

export default DefaultLayout; 