import React, { useState, useEffect } from 'react';
import { Drawer, List, ListItem, ListItemText, Divider, Box, Collapse, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useCharaxy } from '../../contexts/CharaxyContext';
import ExpandLess from '@mui/icons-material/ExpandLess';
import ExpandMore from '@mui/icons-material/ExpandMore';
import { nodeApi } from '../../lib/api';

interface Charaxy {
  id: string;
  title: string;
}

const DefaultSidebar: React.FC = () => {
  const { user, session } = useAuth();
  const { refreshTrigger } = useCharaxy();
  const [charaxies, setCharaxies] = useState<Charaxy[]>([]);
  const [charaxiesOpen, setCharaxiesOpen] = useState(true); // デフォルトは開いた状態

  // キャラクシー一覧を取得
  useEffect(() => {
    const fetchCharaxies = async () => {
      if (!user || !session || !session.access_token) {
        setCharaxies([]);
        return;
      }

      try {
        const data = await nodeApi.getNodes();
        
        // バックエンドからの完全なNodeオブジェクトから必要な部分のみ抽出
        const charaxies = data.map((node: any) => ({
          id: node.id,
          title: node.title
        }));
        setCharaxies(charaxies);
      } catch (error) {
        console.error('キャラクシー取得例外:', error);
      }
    };

    fetchCharaxies();
  }, [user, session, refreshTrigger]); // refreshTriggerが変わったときも再取得

  const handleToggleCharaxies = () => {
    setCharaxiesOpen(!charaxiesOpen);
  };

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: 240,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: 240,
          boxSizing: 'border-box',
          top: 64,
          height: 'calc(100% - 64px)',
          borderTop: 'none',
          position: 'fixed'
        },
      }}
    >
      <Box sx={{ overflow: 'auto' }}>
        <List>
          <ListItem component={RouterLink} to="/dashboard" button>
            <ListItemText primary="ダッシュボード" />
          </ListItem>
          
          <Divider />
          
          {/* CHARAXYグループのヘッダー */}
          <ListItem sx={{ py: 0.5 }}>
            <Typography
              variant="subtitle2"
              sx={{
                fontWeight: 'bold',
                fontSize: '0.8rem',
                color: 'text.secondary',
                letterSpacing: '0.1em'
              }}
            >
              CHARAXY
            </Typography>
          </ListItem>
          
          {/* 自分のキャラクシー一覧 - ユーザーがログインしていれば常に表示 */}
          {user && (
            <>
              <ListItem sx={{ display: 'flex', justifyContent: 'space-between', paddingRight: 1 }}>
                <Box component={RouterLink} to="/charaxy" sx={{ textDecoration: 'none', color: 'inherit', flexGrow: 1 }}>
                  <ListItemText 
                    primary="キャラクシー" 
                  />
                </Box>
                {/* キャラクシーが1件以上ある場合のみ展開/折りたたみボタンを表示 */}
                {charaxies.length > 0 && (
                  <Box 
                    onClick={handleToggleCharaxies} 
                    sx={{ 
                      cursor: 'pointer', 
                      display: 'flex', 
                      alignItems: 'center',
                      p: 0.5,
                      borderRadius: 1,
                      '&:hover': { bgcolor: 'action.hover' }
                    }}
                  >
                    {charaxiesOpen ? <ExpandLess /> : <ExpandMore />}
                  </Box>
                )}
              </ListItem>
              
              {/* キャラクシーが1件以上ある場合の展開リスト */}
              {charaxies.length > 0 && (
                <Collapse in={charaxiesOpen} timeout="auto" unmountOnExit>
                  <List component="div" disablePadding>
                    {charaxies.map(c => (
                      <ListItem 
                        button 
                        component={RouterLink} 
                        to={`/charaxy/edit/${c.id}`} 
                        key={c.id} 
                        sx={{ pl: 4 }}
                      >
                        <ListItemText 
                          primary={c.title}
                          primaryTypographyProps={{ 
                            noWrap: true,
                            style: { 
                              maxWidth: '180px',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis'
                            }
                          }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Collapse>
              )}
            </>
          )}
          <ListItem component={RouterLink} to="/charaxy/themes" button>
            <ListItemText primary="テーマ" />
          </ListItem>
          <ListItem component={RouterLink} to="/charaxy/activity" button>
            <ListItemText primary="みんなの更新" />
          </ListItem>
          <Divider />
          {/* KIOKSグループのヘッダー */}
          <ListItem sx={{ py: 0.5 }}>
            <Typography
              variant="subtitle2"
              sx={{
                fontWeight: 'bold',
                fontSize: '0.8rem',
                color: 'text.secondary',
                letterSpacing: '0.1em'
              }}
            >
              KIOKS
            </Typography>
          </ListItem>
        </List>
      </Box>
    </Drawer>
  );
};

export default DefaultSidebar; 