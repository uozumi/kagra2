import React, { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';

interface CharaxyContextType {
  refreshTrigger: number;
  triggerRefresh: () => void;
}

const CharaxyContext = createContext<CharaxyContextType | undefined>(undefined);

export const CharaxyProvider: React.FC<{children: ReactNode}> = ({ children }) => {
  const [refreshTrigger, setRefreshTrigger] = useState<number>(0);

  // 更新をトリガーする関数
  const triggerRefresh = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <CharaxyContext.Provider value={{ refreshTrigger, triggerRefresh }}>
      {children}
    </CharaxyContext.Provider>
  );
};

// カスタムフック
export const useCharaxy = (): CharaxyContextType => {
  const context = useContext(CharaxyContext);
  if (context === undefined) {
    throw new Error('useCharaxy must be used within a CharaxyProvider');
  }
  return context;
}; 