FROM node:18-alpine

WORKDIR /app

# 依存関係をコピーしてインストール
COPY package*.json ./
RUN npm install

# ソースコードをコピー
COPY . .

# 開発サーバーを起動
EXPOSE 3002
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"] 