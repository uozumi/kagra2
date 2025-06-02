import React from 'react';
import { Typography, Box, Paper, Grid, Card, CardContent } from '@mui/material';
import { Dashboard as DashboardIcon, People as PeopleIcon } from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const Dashboard: React.FC = () => {
  const { user } = useAuth();

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        ダッシュボード
      </Typography>
      
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        システム管理画面へようこそ
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <DashboardIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">
                  システム概要
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                システム管理者として各種設定や管理機能にアクセスできます。
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <PeopleIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">
                  メンバー管理
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                ユーザーの権限管理やシステム管理者権限の付与・削除を行えます。
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              ログイン情報
            </Typography>
            <Typography variant="body2" color="text.secondary">
              ログインユーザー: {user?.email}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              ユーザーID: {user?.id}
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard; 