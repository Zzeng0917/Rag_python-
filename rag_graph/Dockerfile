# GraphRAG - 智能图RAG旅游助手
# 基于 Python 3.11 的 Docker 镜像

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONIOENCODING=utf-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    # OpenCV 依赖
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    # Tesseract OCR (用于 unstructured)
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    # 其他依赖
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirement.txt .

# 安装 Python 依赖
# 注意：torch 安装可能需要较长时间
RUN pip install --upgrade pip && \
    pip install -r requirement.txt

# 复制项目文件
COPY . .

# 创建数据目录
RUN mkdir -p /app/data /app/test_file

# 暴露端口 (如果需要 API 服务)
EXPOSE 8000

# 设置入口点
ENTRYPOINT ["python", "main.py"]

# 默认命令 - 启动交互式界面
CMD ["start"]
