# 使用輕量級的 Python 映像檔
FROM python:3.12-slim

WORKDIR /app

# 安裝系統依賴 (如果需要的話)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 複製並安裝 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案原始碼
COPY . .

# 曝露 Hugging Face 預設的 7860 埠號
EXPOSE 7860

# 啟動命令，讓它自動監聽 7860 或環境變數指定的 PORT
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
