import React, { useEffect, useState } from 'react';
import { Container, Typography, Box, Button, List, ListItem, ListItemText, IconButton, Dialog, DialogTitle, DialogContent, DialogActions, TextField, CircularProgress, Alert, Snackbar, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, ButtonGroup, Paper, TablePagination, LinearProgress } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import { Link as RouterLink } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import CreateTheme from '../../components/modal/CreateTheme';
import CreateThemeBlock from '../../components/modal/CreateThemeBlock';
import { nodeApi, themeApi } from '../../lib/api';
import type { BlockTheme, Node } from '../../types';

interface ThemeWithCount {
  id: string;
  title: string;
  updated_at?: string;
  block_count: number;
  creator_id?: string;
}

// ソートの種類を定義
type SortType = 'title' | 'titleDesc' | 'updated' | 'updatedDesc' | 'count' | 'countDesc';

const ThemeList: React.FC = () => {
  const [themes, setThemes] = useState<BlockTheme[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [blockModalOpen, setBlockModalOpen] = useState(false);
  const [blockModalTheme, setBlockModalTheme] = useState<ThemeWithCount | null>(null);
  const [userNodes, setUserNodes] = useState<Node[]>([]);
  const [noNodeAlertOpen, setNoNodeAlertOpen] = useState(false);
  const { user, session } = useAuth();
  const [sortType, setSortType] = useState<SortType>('updatedDesc'); // 初期値は更新新しい順
  const [search, setSearch] = useState('');
  const [hoveredRow, setHoveredRow] = useState<string | null>(null);
  // ページネーション用のstate
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(50);

  const fetchThemes = async () => {
    try {
      const themesData = await themeApi.getThemes();
      setThemes(themesData || []);
    } catch (error: any) {
      console.error('テーマ取得エラー:', error);
      setError(error.message || 'テーマの取得に失敗しました');
    }
  };

  const fetchNodes = async () => {
    if (!user || !session?.access_token) return;
    
    try {
      const nodesData = await nodeApi.getNodes();
      setUserNodes(nodesData || []);
    } catch (error) {
      console.error('ノード取得エラー:', error);
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      
      await Promise.all([
        fetchThemes(),
        fetchNodes()
      ]);
      
      setLoading(false);
    };

    if (user && session?.access_token) {
      fetchData();
    }
  }, [user, session?.access_token]);

  const openCreateModal = () => {
    setModalOpen(true);
  };

  const handleSaveTheme = async (title: string) => {
    try {
      await themeApi.createTheme({ title: title.trim() });
      
      // テーマ一覧を再取得
      await fetchThemes();
      setModalOpen(false);
    } catch (error: any) {
      console.error('テーマ保存エラー:', error);
      setError(error.message || '保存中にエラーが発生しました');
    }
  };

  // ブロック追加モーダルのonSuccessでテーマ一覧を再取得
  const handleBlockCreateSuccess = () => {
    fetchThemes();
  };

  // ソート方向を切り替える関数
  const handleSort = (column: 'title' | 'updated' | 'count') => {
    const currentSortType = sortType;
    
    // 現在のソートと同じカラムなら昇順・降順を切り替え、違うカラムなら降順から開始
    if (column === 'title') {
      setSortType(currentSortType === 'title' ? 'titleDesc' : 'title');
    } else if (column === 'updated') {
      setSortType(currentSortType === 'updated' ? 'updatedDesc' : 'updated');
    } else if (column === 'count') {
      setSortType(currentSortType === 'count' ? 'countDesc' : 'count');
    }
  };

  // ソートアイコンを表示する関数
  const renderSortIcon = (column: 'title' | 'updated' | 'count') => {
    // 現在のソートがこのカラムに関係するか確認
    let isSorted = false;
    let isAsc = false;
    
    if (column === 'title') {
      isSorted = sortType === 'title' || sortType === 'titleDesc';
      isAsc = sortType === 'title';
    } else if (column === 'updated') {
      isSorted = sortType === 'updated' || sortType === 'updatedDesc';
      isAsc = sortType === 'updated';
    } else if (column === 'count') {
      isSorted = sortType === 'count' || sortType === 'countDesc';
      isAsc = sortType === 'count';
    }
    
    // ソートされていない場合は何も表示しない
    if (!isSorted) return null;
    
    // 昇順・降順アイコンを表示
    return isAsc ? <ArrowUpwardIcon fontSize="small" /> : <ArrowDownwardIcon fontSize="small" />;
  };

  const filteredThemes = themes
    .filter(t => t.title.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => {
      if (sortType === 'title') return a.title.localeCompare(b.title);
      if (sortType === 'titleDesc') return b.title.localeCompare(a.title);
      if (sortType === 'updated') return (a.updated_at || '').localeCompare(b.updated_at || '');
      if (sortType === 'updatedDesc') return (b.updated_at || '').localeCompare(a.updated_at || '');
      if (sortType === 'count') return (a.block_count || 0) - (b.block_count || 0);
      if (sortType === 'countDesc') return (b.block_count || 0) - (a.block_count || 0);
      return 0;
    });
    
  // 現在のページに表示する行を取得
  const paginatedThemes = filteredThemes.slice(
    page * rowsPerPage, 
    page * rowsPerPage + rowsPerPage
  );

  // ページ変更ハンドラー
  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  // 1ページの行数変更ハンドラー
  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0); // ページをリセット
  };

  // テーマ名セル
  const ThemeTitleCell = ({ theme }: { theme: BlockTheme }) => {
    return (
      <Box display="flex" alignItems="center">
        <Typography
          component={RouterLink}
          to={`/charaxy/themes/${theme.id}`}
          color="primary"
          sx={{ textDecoration: 'underline', cursor: 'pointer', mr: 1 }}
        >
          {theme.title}
        </Typography>
      </Box>
    );
  };

  // 更新日時セル - マウスホバー時のみ表示（opacity制御）
  const UpdatedAtCell = ({ theme }: { theme: BlockTheme }) => {
    const isHovered = hoveredRow === theme.id;
    const dateText = theme.updated_at 
      ? new Date(theme.updated_at).toLocaleDateString('ja-JP') 
      : '';
    
    return (
      <TableCell>
        <Typography
          variant="caption"
          sx={{
            opacity: isHovered ? 1 : 0,
            transition: 'opacity 0.2s ease-in-out',
            minWidth: '80px', // 最小幅を設定してガタつきを防止
            display: 'inline-block'
          }}
        >
          {dateText}
        </Typography>
      </TableCell>
    );
  };

  if (loading) {
    return (
      <Container sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  // エラーがあっても基本的なUIは表示する
  return (
    <Container 
      maxWidth="md" 
      sx={{ 
        mt: 4,
        ml: 0,
        mr: 'auto'
      }}
    >
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" gutterBottom>テーマ一覧</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={openCreateModal}>
          作成
        </Button>
      </Box>

      {error && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <TableContainer component={Paper} sx={{ mb: 2 }}>
        <Box 
          display="flex" 
          alignItems="center" 
          justifyContent="space-between" 
          p={2}
          sx={{ 
            borderBottom: 1, 
            borderColor: 'divider', 
            pb: 1.5 
          }}
        >
          <TextField
            size="small"
            placeholder="キーワード検索"
            value={search}
            onChange={e => setSearch(e.target.value)}
            sx={{ width: 240 }}
          />
          <TablePagination
            rowsPerPageOptions={[10, 25, 50, 100]}
            component="div"
            count={filteredThemes.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
            labelRowsPerPage="表示件数:"
            labelDisplayedRows={({ from, to, count }) => `${from}-${to} / ${count}`}
            sx={{ border: 'none', m: 0, p: 0 }} // 余分な余白やボーダーを削除
          />
        </Box>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell 
                onClick={() => handleSort('title')}
                sx={{ 
                  cursor: 'pointer', 
                  userSelect: 'none',
                  backgroundColor: sortType === 'title' || sortType === 'titleDesc' ? 'rgba(0, 0, 0, 0.04)' : 'inherit'
                }}
              >
                <Box display="flex" alignItems="center">
                  <Typography variant="subtitle2" fontWeight="bold">テーマ名</Typography>
                  {renderSortIcon('title')}
                </Box>
              </TableCell>
              <TableCell 
                onClick={() => handleSort('updated')}
                sx={{ 
                  cursor: 'pointer', 
                  userSelect: 'none',
                  backgroundColor: sortType === 'updated' || sortType === 'updatedDesc' ? 'rgba(0, 0, 0, 0.04)' : 'inherit'
                }}
              >
                <Box display="flex" alignItems="center">
                  <Typography variant="subtitle2" fontWeight="bold">更新日時</Typography>
                  {renderSortIcon('updated')}
                </Box>
              </TableCell>
              <TableCell 
                onClick={() => handleSort('count')}
                sx={{ 
                  cursor: 'pointer', 
                  userSelect: 'none',
                  backgroundColor: sortType === 'count' || sortType === 'countDesc' ? 'rgba(0, 0, 0, 0.04)' : 'inherit'
                }}
              >
                <Box display="flex" alignItems="center">
                  <Typography variant="subtitle2" fontWeight="bold">回答数</Typography>
                  {renderSortIcon('count')}
                </Box>
              </TableCell>
              <TableCell>
                <Typography variant="subtitle2" fontWeight="bold">書く</Typography>
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedThemes.length > 0 ? (
              paginatedThemes.map(theme => (
                <TableRow 
                  key={theme.id}
                  onMouseEnter={() => setHoveredRow(theme.id)}
                  onMouseLeave={() => setHoveredRow(null)}
                  hover
                >
                  <TableCell>
                    <ThemeTitleCell theme={theme} />
                  </TableCell>
                  <UpdatedAtCell theme={theme} />
                  <TableCell>
                    <Button
                      size="small"
                      variant="outlined"
                      color="info"
                      component={RouterLink}
                      to={`/charaxy/themes/${theme.id}`}
                      sx={{ 
                          minWidth: '70px',    // 最小幅を設定
                          width: '70px',       // 幅を固定
                          textAlign: 'center'  // テキストを中央揃え
                        }}
                      >
                        {theme.block_count || 0}件
                      </Button>
                  </TableCell>
                  <TableCell>
                    <IconButton
                      size="small"
                      color="primary"
                      sx={{ mr: 1 }}
                      onClick={() => {
                        if (userNodes.length === 0) {
                          setNoNodeAlertOpen(true);
                        } else {
                          setBlockModalTheme(theme as ThemeWithCount);
                          setBlockModalOpen(true);
                        }
                      }}
                    >
                      <EditIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={4} align="center">
                  <Typography variant="body2" color="text.secondary" sx={{ py: 4 }}>
                    {error ? 'データの読み込みに問題があります' : 'テーマがありません'}
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
      
      {/* テーマ作成モーダル */}
      <CreateTheme
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onSave={handleSaveTheme}
        maxLength={100}
      />
      
      {/* 共通ブロック追加モーダル */}
      {blockModalTheme && userNodes.length > 0 && (
        <CreateThemeBlock
          open={blockModalOpen}
          onClose={() => setBlockModalOpen(false)}
          theme={{ id: blockModalTheme.id, title: blockModalTheme.title }}
          onSuccess={handleBlockCreateSuccess}
          titleMaxLength={100}
          contentMaxLength={400}
        />
      )}

      <Snackbar
        open={noNodeAlertOpen}
        autoHideDuration={4000}
        onClose={() => setNoNodeAlertOpen(false)}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert severity="warning" onClose={() => setNoNodeAlertOpen(false)} sx={{ width: '100%' }}>
          まずは
          <RouterLink to="/charaxy/" style={{ textDecoration: 'underline', color: '#1976d2', margin: '0 4px' }}>
            キャラクシーを作ってください
          </RouterLink>
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default ThemeList; 