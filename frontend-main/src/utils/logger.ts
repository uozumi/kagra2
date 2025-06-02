// ログレベルの定義
type LogLevel = 'debug' | 'log' | 'warn' | 'error';

interface Logger {
  debug: (...args: any[]) => void;
  log: (...args: any[]) => void;
  warn: (...args: any[]) => void;
  error: (...args: any[]) => void;
}

// 開発環境かどうかの判定
const isDevelopment = import.meta.env.MODE === 'development';

// ログレベルの設定（環境変数から取得、デフォルトは'log'）
const logLevel = import.meta.env.VITE_LOG_LEVEL || 'log';

// ログレベルの優先度
const logLevels: Record<LogLevel, number> = {
  debug: 0,
  log: 1,
  warn: 2,
  error: 3,
};

// 現在のログレベルの優先度
const currentLogLevel = logLevels[logLevel as LogLevel] || logLevels.log;

// ログ出力関数
const createLogFunction = (level: LogLevel, consoleFn: (...args: any[]) => void) => {
  return (...args: any[]) => {
    // 本番環境では error と warn のみ出力
    if (!isDevelopment && level !== 'error' && level !== 'warn') {
      return;
    }
    
    // ログレベルフィルタリング
    if (logLevels[level] < currentLogLevel) {
      return;
    }
    
    const timestamp = new Date().toISOString();
    const prefix = `[${timestamp}] [${level.toUpperCase()}]`;
    
    consoleFn(prefix, ...args);
  };
};

// ロガーオブジェクトの作成
const logger: Logger = {
  debug: createLogFunction('debug', console.debug),
  log: createLogFunction('log', console.log),
  warn: createLogFunction('warn', console.warn),
  error: createLogFunction('error', console.error),
};

export default logger; 