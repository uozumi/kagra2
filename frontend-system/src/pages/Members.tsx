import React, { useEffect, useState } from 'react';
import {
  Typography,
  Paper,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Chip,
  CircularProgress,
  Alert,
  Snackbar,
  Tooltip
} from '@mui/material';
import { systemApi } from '../lib/api';
import logger from '../utils/logger';
import { useAuth } from '../contexts/AuthContext';
import type { User } from '../types';

const AdminSystemMembers: React.FC = () => {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [processingUserId, setProcessingUserId] = useState<string | null>(null);

  // 全ユーザーとシステム管理者権限の取得
  const fetchUsers = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // FastAPI経由で全ユーザーとその権限情報を取得
      const usersData = await systemApi.getUsers();
      setUsers(usersData);
    } catch (err) {
      logger.error('ユーザー情報取得エラー:', err);
      setError('ユーザー情報の取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  // 初回ロード時にユーザー情報を取得
  useEffect(() => {
    fetchUsers();
  }, []);

  // 管理者権限の付与
  const grantAdminPermission = async (userId: string) => {
    setProcessingUserId(userId);
    setError(null);
    
    try {
      await systemApi.grantAdminPermission(userId);
      
      // ユーザーリストの更新
      setUsers(prevUsers => 
        prevUsers.map(user => 
          user.id === userId 
            ? { ...user, is_system_admin: true } 
            : user
        )
      );
      
      setSuccessMessage('システム管理者権限を付与しました');
    } catch (err) {
      logger.error('権限付与エラー:', err);
      setError('システム管理者権限の付与に失敗しました');
    } finally {
      setProcessingUserId(null);
    }
  };

  // 管理者権限の削除
  const revokeAdminPermission = async (userId: string) => {
    // 自分自身の権限は削除できないようにする
    if (userId === currentUser?.id) {
      setError('自分自身の権限は削除できません');
      return;
    }
    
    setProcessingUserId(userId);
    setError(null);
    
    try {
      await systemApi.revokeAdminPermission(userId);
      
      // ユーザーリストの更新
      setUsers(prevUsers => 
        prevUsers.map(user => 
          user.id === userId 
            ? { ...user, is_system_admin: false } 
            : user
        )
      );
      
      setSuccessMessage('システム管理者権限を削除しました');
    } catch (err) {
      logger.error('権限削除エラー:', err);
      setError('システム管理者権限の削除に失敗しました');
    } finally {
      setProcessingUserId(null);
    }
  };

  // 成功メッセージのクリア
  const handleCloseSuccessMessage = () => {
    setSuccessMessage(null);
  };

  // 自分自身かどうかを判定
  const isSelf = (userId: string) => currentUser?.id === userId;

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        メンバー管理
      </Typography>
      
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        システム管理画面にアクセスできるユーザーを管理します。
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      
      <Snackbar
        open={Boolean(successMessage)}
        autoHideDuration={3000}
        onClose={handleCloseSuccessMessage}
        message={successMessage}
      />
      
      <Paper sx={{ width: '100%', mb: 4 }}>
        <TableContainer>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>ユーザー</TableCell>
                  <TableCell>メールアドレス</TableCell>
                  <TableCell>登録日</TableCell>
                  <TableCell>システム管理者</TableCell>
                  <TableCell>アクション</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {users.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell>
                      {user.name || '名前未設定'}
                      {isSelf(user.id) && (
                        <Chip size="small" label="自分" color="success" sx={{ ml: 1 }} />
                      )}
                    </TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>
                      {new Date(user.created_at).toLocaleDateString('ja-JP')}
                    </TableCell>
                    <TableCell>
                      {user.is_system_admin ? (
                        <Chip color="primary" label="管理者" />
                      ) : (
                        <Chip variant="outlined" label="一般ユーザー" />
                      )}
                    </TableCell>
                    <TableCell>
                      {processingUserId === user.id ? (
                        <CircularProgress size={24} />
                      ) : user.is_system_admin ? (
                        isSelf(user.id) ? (
                          <Tooltip title="自分自身の権限は削除できません">
                            <span>
                              <Button
                                variant="outlined"
                                color="error"
                                size="small"
                                disabled
                              >
                                権限削除
                              </Button>
                            </span>
                          </Tooltip>
                        ) : (
                          <Button
                            variant="outlined"
                            color="error"
                            size="small"
                            onClick={() => revokeAdminPermission(user.id)}
                          >
                            権限削除
                          </Button>
                        )
                      ) : (
                        <Button
                          variant="contained"
                          color="primary"
                          size="small"
                          onClick={() => grantAdminPermission(user.id)}
                        >
                          権限付与
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </TableContainer>
      </Paper>
    </Box>
  );
};

export default AdminSystemMembers; 