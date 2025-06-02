import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { CssBaseline } from '@mui/material';
import { AuthProvider } from './contexts/AuthContext';
import { CharaxyProvider } from './contexts/CharaxyContext';
import RouteGuard from './components/RouteGuard';

// レイアウト
import LandingLayout from './layouts/LandingLayout';
import DefaultLayout from './layouts/DefaultLayout';

// ページ
import Landing from './pages/Landing';
import Dashboard from './pages/Dashboard';
import Account from './pages/Account';
import CharaxyList from './pages/charaxy/CharaxyList';
import CharaxyDetail from './pages/charaxy/CharaxyDetail';
import ThemeList from './pages/charaxy/ThemeList';
import ThemeDetail from './pages/charaxy/ThemeDetail';
import Activity from './pages/charaxy/Activity';

const App = () => {
  return (
    <>
      <CssBaseline />
      <AuthProvider>
        <CharaxyProvider>
          <BrowserRouter>
            <Routes>
              {/* ランディングページ */}
              <Route
                path="/"
                element={
                  <RouteGuard
                    element={
                      <LandingLayout>
                        <Landing />
                      </LandingLayout>
                    }
                    requireAuth={false}
                    redirectPath="/dashboard"
                  />
                }
              />

              {/* ダッシュボード */}
              <Route
                path="/dashboard"
                element={
                  <RouteGuard
                    element={
                      <DefaultLayout>
                        <Dashboard />
                      </DefaultLayout>
                    }
                    requireAuth={true}
                  />
                }
              />

              {/* アカウント設定 */}
              <Route
                path="/account"
                element={
                  <RouteGuard
                    element={
                      <DefaultLayout>
                        <Account />
                      </DefaultLayout>
                    }
                    requireAuth={true}
                  />
                }
              />

              {/* キャラクシー一覧 */}
              <Route
                path="/charaxy"
                element={
                  <RouteGuard
                    element={
                      <DefaultLayout>
                        <CharaxyList />
                      </DefaultLayout>
                    }
                    requireAuth={true}
                  />
                }
              />

              {/* キャラクシーテーマ */}
              <Route
                path="/charaxy/themes"
                element={
                  <RouteGuard
                    element={
                      <DefaultLayout>
                        <ThemeList />
                      </DefaultLayout>
                    }
                    requireAuth={true}
                  />
                }
              />

              {/* テーマ詳細 */}
              <Route
                path="/charaxy/themes/:themeId"
                element={
                  <RouteGuard
                    element={
                      <DefaultLayout>
                        <ThemeDetail />
                      </DefaultLayout>
                    }
                    requireAuth={true}
                  />
                }
              />

              {/* キャラクシーアクティビティ */}
              <Route
                path="/charaxy/activity"
                element={
                  <RouteGuard
                    element={
                      <DefaultLayout>
                        <Activity />
                      </DefaultLayout>
                    }
                    requireAuth={true}
                  />
                }
              />

              {/* キャラクシー編集 */}
              <Route
                path="/charaxy/edit/:nodeId"
                element={
                  <RouteGuard
                    element={
                      <DefaultLayout>
                        <CharaxyDetail />
                      </DefaultLayout>
                    }
                    requireAuth={true}
                  />
                }
              />

              {/* キャラクシー特定ブロック表示 */}
              <Route
                path="/charaxy/:nodeId/:blockId"
                element={
                  <RouteGuard
                    element={
                      <DefaultLayout>
                        <CharaxyDetail />
                      </DefaultLayout>
                    }
                    requireAuth={true}
                  />
                }
              />

              {/* キャラクシー詳細 */}
              <Route
                path="/charaxy/:nodeId"
                element={
                  <RouteGuard
                    element={
                      <DefaultLayout>
                        <CharaxyDetail />
                      </DefaultLayout>
                    }
                    requireAuth={true}
                  />
                }
              />

              {/* 404 - 認証済みユーザーはダッシュボードへ、未認証はランディングへ */}
              <Route 
                path="*" 
                element={
                  <RouteGuard
                    element={<Navigate to="/dashboard" replace />}
                    requireAuth={true}
                    redirectPath="/"
                  />
                } 
              />
            </Routes>
          </BrowserRouter>
        </CharaxyProvider>
      </AuthProvider>
    </>
  );
};

export default App;
