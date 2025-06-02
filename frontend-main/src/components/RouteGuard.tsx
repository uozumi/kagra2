import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { CircularProgress, Box } from '@mui/material';

interface RouteGuardProps {
  element: React.ReactElement;
  requireAuth: boolean;
  redirectPath?: string;
}

const RouteGuard: React.FC<RouteGuardProps> = ({ 
  element, 
  requireAuth, 
  redirectPath = '/' 
}) => {
  const { user, loading } = useAuth();

  // 認証状態の読み込み中
  if (loading) {
    return (
      <Box 
        display="flex" 
        justifyContent="center" 
        alignItems="center" 
        minHeight="100vh"
      >
        <CircularProgress />
      </Box>
    );
  }

  // 認証が必要なページで未認証の場合
  if (requireAuth && !user) {
    return <Navigate to={redirectPath} replace />;
  }

  // 認証が不要なページで認証済みの場合
  if (!requireAuth && user) {
    return <Navigate to={redirectPath} replace />;
  }

  // 条件を満たしている場合は要素を表示
  return element;
};

export default RouteGuard; 