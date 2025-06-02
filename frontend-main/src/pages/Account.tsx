import React, { useEffect, useState } from 'react';
import { Container, Typography, Paper, Box, Button, TextField, List, ListItem, ListItemText, CircularProgress, Alert, Snackbar } from '@mui/material';
import { useAuth } from '../contexts/AuthContext';
import { supabase } from '../lib/supabase';
import { useAsyncState } from '../hooks/useAsyncState';

interface Affiliation {
  user_id: string;
  tenant_id: string;
  tenant_name: string;
  department_id: string | null;
  department_name: string | null;
  created_at: string;
}

interface AccountData {
  name: string;
  slackId: string;
  extension: string;
  tenantDepartments: { tenantId: string, tenantName: string, departments: string[] }[];
}

const Account: React.FC = () => {
  const { user, signOut } = useAuth();
  const [name, setName] = useState('');
  const [slackId, setSlackId] = useState('');
  const [extension, setExtension] = useState('');
  const [success, setSuccess] = useState<string | null>(null);
  const [tenantDepartments, setTenantDepartments] = useState<{ tenantId: string, tenantName: string, departments: string[] }[]>([]);
  
  // データ取得用の非同期状態管理
  const dataState = useAsyncState<AccountData>(true);
  
  // 保存用の非同期状態管理
  const saveState = useAsyncState<void>(false);

  useEffect(() => {
    const fetchData = async (): Promise<AccountData> => {
      if (!user) throw new Error('ユーザーが見つかりません');
      
      // Supabaseセッションからアクセストークンを取得
      const { data: { session } } = await supabase.auth.getSession();
      
      // FastAPI経由でユーザー情報を取得
      const response = await fetch('/api/v1/users/me', {
        headers: {
          'Authorization': `Bearer ${session?.access_token || ''}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`ユーザー情報取得エラー: ${response.status}`);
      }
      
      const userData = await response.json();
      
      return {
        name: userData.name || '',
        slackId: userData.slack_member_id || '',
        extension: userData.extension_number || '',
        tenantDepartments: userData.affiliations || []
      };
    };

    if (user) {
      dataState.execute(fetchData).then((data) => {
        setName(data.name);
        setSlackId(data.slackId);
        setExtension(data.extension);
        setTenantDepartments(data.tenantDepartments);
      }).catch(() => {
        // エラーはuseAsyncStateで管理
      });
    }
  }, [user]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    
    setSuccess(null);
    
    const saveData = async (): Promise<void> => {
      // Supabaseセッションからアクセストークンを取得
      const { data: { session } } = await supabase.auth.getSession();
      
      // FastAPI経由でユーザー情報を更新
      const response = await fetch('/api/v1/users/me', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${session?.access_token || ''}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: name.trim(),
          slack_member_id: slackId.trim(),
          extension_number: extension.trim()
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `更新エラー: ${response.status}`);
      }
    };
    
    try {
      await saveState.execute(saveData);
      setSuccess('保存しました');
      // 3秒後に自動で非表示
      setTimeout(() => setSuccess(null), 3000);
    } catch (error) {
      // エラーはuseAsyncStateで管理
    }
  };

  const handleCloseSnackbar = () => {
    setSuccess(null);
  };

  const handleSignOut = async () => {
    await signOut();
  };

  if (dataState.loading) {
    return (
      <Container maxWidth="md" sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        アカウント
      </Typography>
      <Typography variant="body1" paragraph>
        あなたのアカウント情報を編集できます。
      </Typography>
      <Paper sx={{ p: 2 }}>
        <Box component="form" onSubmit={handleSave} sx={{ mt: 2, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
          <Typography variant="h6" gutterBottom>基本情報</Typography>
          <TextField
            label="名前"
            value={name}
            onChange={e => setName(e.target.value)}
            fullWidth
            sx={{ mb: 2 }}
          />
          <TextField
            label="SlackメンバーID"
            value={slackId}
            onChange={e => setSlackId(e.target.value)}
            fullWidth
            sx={{ mb: 2 }}
          />
          <TextField
            label="内線番号"
            value={extension}
            onChange={e => setExtension(e.target.value)}
            fullWidth
            sx={{ mb: 2 }}
          />
          <Button type="submit" variant="contained" color="primary" disabled={saveState.loading} sx={{ mt: 1 }}>
            {saveState.loading ? <CircularProgress size={20} color="inherit" /> : '保存'}
          </Button>
          {(dataState.error || saveState.error) && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {dataState.error || saveState.error}
            </Alert>
          )}
        </Box>
      </Paper>
      <Paper sx={{ p: 2, mt: 4 }}>
        <Box sx={{ bgcolor: 'background.default', borderRadius: 1 }}>
          <Typography variant="h6" gutterBottom>所属</Typography>
          {tenantDepartments.length === 0 ? (
            <Typography variant="body2">所属情報なし</Typography>
          ) : (
            <List>
              {tenantDepartments.map(td => (
                <React.Fragment key={td.tenantId}>
                  <ListItem sx={{ bgcolor: 'grey.100', borderRadius: 1 }}>
                    <ListItemText primary={td.tenantName} primaryTypographyProps={{ fontWeight: 'bold' }} />
                  </ListItem>
                  {td.departments.length === 0 ? (
                    <ListItem sx={{ pl: 4 }}>
                      <ListItemText primary="部署不明" />
                    </ListItem>
                  ) : td.departments.map((dept, i) => (
                    <ListItem key={i} sx={{ pl: 4 }}>
                      <ListItemText primary={dept} />
                    </ListItem>
                  ))}
                </React.Fragment>
              ))}
            </List>
          )}
        </Box>
      </Paper>
      
      {/* 成功メッセージのスナックバー */}
      <Snackbar
        open={!!success}
        autoHideDuration={3000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        message={success}
      />
    </Container>
  );
};

export default Account; 