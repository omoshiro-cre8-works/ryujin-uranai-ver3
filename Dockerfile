FROM python:3.11-slim

# OSのライブラリ（PDF作成に必要）をインストール
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 全ファイルをコピー
COPY . .

# ライブラリをインストール
RUN pip install --no-cache-dir -r requirements.txt

# Streamlitをポート8080で起動する命令
CMD ["streamlit", "run", "app.py", "--server.port", "8080", "--server.address", "0.0.0.0"]