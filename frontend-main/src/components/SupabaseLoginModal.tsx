import React, { useEffect, useState } from 'react';
import {
  Modal, 
  Box,
  Typography,
  IconButton
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { Auth } from '@supabase/auth-ui-react';
import { ThemeSupa } from '@supabase/auth-ui-shared';
import { supabase } from '../lib/supabase';
import logger from '../utils/logger';
import { useAuth } from '../contexts/AuthContext';

interface SupabaseLoginModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
}

const SupabaseLoginModal: React.FC<SupabaseLoginModalProps> = ({ 
  open, 
  onClose, 
  title = 'ログイン' 
}) => {
  const { user } = useAuth();
  const [redirectUrl, setRedirectUrl] = useState<string>('');
  
  // リダイレクトURLを設定
  useEffect(() => {
    // 開発環境とプロダクション環境で同じURLフォーマットを使用する
    const url = window.location.origin + '/';
    setRedirectUrl(url);
    logger.log('設定したリダイレクトURL:', url);
  }, []);
  
  // デバッグ用：現在のURIを表示
  useEffect(() => {
    if (open) {
      logger.log('現在のURL:', window.location.href);
      logger.log('ホスト部分:', window.location.origin);
      logger.log('パス部分:', window.location.pathname);
    }
  }, [open]);

  // ユーザーがログインしたらモーダルを閉じる
  useEffect(() => {
    if (user && open) {
      onClose();
    }
  }, [user, open, onClose]);

  return (
    <Modal 
      open={open} 
      onClose={onClose}
      aria-labelledby="supabase-login-modal"
    >
      <Box sx={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: 400,
        bgcolor: 'background.paper',
        boxShadow: 24,
        p: 4,
        borderRadius: 2,
        maxHeight: '90vh',
        overflow: 'auto'
      }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography id="supabase-login-modal" variant="h6" component="h2">
            {title}
          </Typography>
          <IconButton 
            aria-label="close" 
            onClick={onClose}
            size="small"
          >
            <CloseIcon />
          </IconButton>
        </Box>

        {redirectUrl && (
          <Auth
            supabaseClient={supabase}
            appearance={{
              theme: ThemeSupa,
              style: {
                button: {
                  borderRadius: '4px',
                },
                input: {
                  borderRadius: '4px',
                },
              },
            }}
            theme="light"
            providers={['google']}
            view="sign_in"
            redirectTo={redirectUrl}
            localization={{
              variables: {
                sign_in: {
                  email_label: 'メールアドレス',
                  password_label: 'パスワード',
                  button_label: 'ログイン',
                  loading_button_label: 'ログイン中...',
                  link_text: 'アカウントをお持ちの方はログイン',
                  social_provider_text: "Googleでログイン",
                },
                sign_up: {
                  email_label: 'メールアドレス',
                  password_label: 'パスワード',
                  button_label: '新規登録',
                  loading_button_label: '登録中...',
                  link_text: '新規登録はこちら',
                  social_provider_text: "Googleで登録",
                },
              },
            }}
          />
        )}
      </Box>
    </Modal>
  );
};

export default SupabaseLoginModal; 