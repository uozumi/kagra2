import React, { useState, useEffect } from 'react';
import { Container, Typography, Box, Paper, Grid, Card, CardContent, Button, CircularProgress } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface DashboardStats {
  charaxiesCount: number;
  blocksCount: number;
  themesCount: number;
}

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats>({
    charaxiesCount: 0,
    blocksCount: 0,
    themesCount: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 統計情報の取得（APIが必要）
    const fetchStats = async () => {
      try {
        // 暫定的にダミーデータを設定
        setStats({
          charaxiesCount: 0,
          blocksCount: 0,
          themesCount: 0
        });
      } catch (error) {
        console.error('統計情報の取得に失敗:', error);
      } finally {
        setLoading(false);
      }
    };

    if (user) {
      fetchStats();
    } else {
      setLoading(false);
    }
  }, [user]);

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h3" component="h1" gutterBottom>
        KAGRA
      </Typography>
      
      <Typography variant="h5" color="text.secondary" paragraph>
        Knowledge Architecture for Generative Research Activities
      </Typography>

      <Paper sx={{ p: 4, mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          ようこそ、KAGRAへ
        </Typography>
        
        <Typography variant="body1" paragraph>
          KAGRAは研究活動を支援するナレッジアーキテクチャプラットフォームです。
          キャラクシーとPersonarという2つの主要機能を通じて、あなたの研究活動をサポートします。
        </Typography>

        <Grid container spacing={3} sx={{ mt: 2 }}>
          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  キャラクシー (Charaxy)
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  研究のアイデアや知見を構造化して管理できます。
                  ブロック単位で情報を整理し、テーマ別に分類することで、
                  研究の進捗を可視化できます。
                </Typography>
                <Button 
                  component={RouterLink} 
                  to="/charaxy" 
                  variant="contained" 
                  color="primary"
                >
                  キャラクシーを始める
                </Button>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Personar
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  研究者のプロファイルと専門性を管理し、
                  コラボレーションの機会を発見できます。
                  （開発予定）
                </Typography>
                <Button 
                  variant="outlined" 
                  disabled
                >
                  近日公開
                </Button>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {user && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h5" gutterBottom>
            あなたの統計
          </Typography>
          
          <Grid container spacing={3}>
            <Grid item xs={12} sm={4}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="primary">
                    {stats.charaxiesCount}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    キャラクシー
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} sm={4}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="primary">
                    {stats.blocksCount}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    ブロック
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} sm={4}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="primary">
                    {stats.themesCount}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    テーマ
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Paper>
      )}
    </Container>
  );
};

export default Dashboard; 