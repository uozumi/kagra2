import React, { useState } from 'react';
import { Box, Typography, Button, Paper, Grid, Container } from '@mui/material';
import { useAuth } from '../contexts/AuthContext';
import SupabaseLoginModal from '../components/SupabaseLoginModal';

const Landing: React.FC = () => {
  const { user } = useAuth();
  const [loginOpen, setLoginOpen] = useState(false);

  const handleOpenLogin = () => {
    setLoginOpen(true);
  };

  const handleCloseLogin = () => {
    setLoginOpen(false);
  };

  return (
    <Box>
      <Grid container spacing={4} justifyContent="center">
        <Grid item xs={12} textAlign="center">
          <Typography variant="h2" component="h1" gutterBottom>
            KAGRA
          </Typography>

          {!user && (
            <Button 
              variant="contained" 
              size="large"
              color="primary" 
              onClick={handleOpenLogin}
              sx={{ mt: 2, mb: 4 }}
            >
              はじめる
            </Button>
          )}
        </Grid>
      </Grid>
      <SupabaseLoginModal open={loginOpen} onClose={handleCloseLogin} />
    </Box>
  );
};

export default Landing; 