import React, { useEffect, useState } from 'react';
import { Container, Typography, Box, CircularProgress, Alert, Paper, List, ListItem } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { activityApi } from '../../lib/api';

interface ActivityItem {
  block_id: string;
  block_title: string;
  block_updated_at: string;
  node_title: string;
  user_name: string;
  user_id: string;
  node_id: string;
}

const Activity: React.FC = () => {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user, session } = useAuth();

  useEffect(() => {
    const fetchActivity = async () => {
      if (!user || !session?.access_token) return;
      
      setLoading(true);
      setError(null);
      
      try {
        const activitiesData = await activityApi.getActivity();
        setActivities(activitiesData || []);
      } catch (error: any) {
        console.error('アクティビティ取得エラー:', error);
        setError(error.message || 'アクティビティの取得に失敗しました');
      } finally {
        setLoading(false);
      }
    };

    fetchActivity();
  }, [user, session?.access_token]);

  if (loading) {
    return (
      <Container sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error) {
    return (
      <Container sx={{ mt: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  return (
    <Container 
      maxWidth="md" 
      sx={{ 
        mt: 4,
        ml: 0,
        mr: 'auto'
      }}
    >
      <Typography variant="h4" gutterBottom>みんなの更新</Typography>
      <Paper sx={{ p: 4 }}>
        <List>
          {activities.length === 0 ? (
            <Typography variant="body1">公開された更新はまだありません。</Typography>
          ) : (
            activities.map((item) => (
              <ListItem key={item.block_id} sx={{ py: 2, px: 0 }} divider>
                <Box sx={{ width: '100%' }}>
                  <Typography variant="body1" sx={{ display: 'inline' }}>
                    {item.user_name} さんが「
                  </Typography>
                  <Typography
                    component={RouterLink}
                    to={`/charaxy/${item.node_id}/${item.block_id}`}
                    color="primary"
                    sx={{ textDecoration: 'underline', display: 'inline', mx: 0.5 }}
                  >
                    {item.block_title}
                  </Typography>
                  （<Typography
                    variant="body2"
                    color="text.secondary"
                    component={RouterLink}
                    to={`/charaxy/${item.node_id}`}
                    sx={{ textDecoration: 'underline', display: 'inline' }}
                  >
                    {item.node_title}
                  </Typography>）
                  <Typography variant="body1" sx={{ display: 'inline' }}>
                    」を更新
                  </Typography>
                  <br />
                  <Typography variant="caption" color="text.secondary" sx={{ mr: 1 }}>
                    {new Date(item.block_updated_at).toLocaleString('ja-JP')}
                  </Typography>
                </Box>
              </ListItem>
            ))
          )}
        </List>
      </Paper>
    </Container>
  );
};

export default Activity; 