# 后端 Dockerfile
# 使用多阶段构建优化镜像大小

# 阶段1: 构建依赖
FROM python:3.11-slim AS builder

WORKDIR /app

# 复制项目文件（用于安装依赖）
COPY pyproject.toml uv.lock README.md ./

# 安装 uv 并创建虚拟环境，安装所有依赖
# 使用阿里云镜像源（如果失败可尝试其他源）
RUN pip install -i https://mirrors.aliyun.com/pypi/simple/ uv && \
    uv venv /opt/venv && \
    uv pip install --python /opt/venv/bin/python -i https://mirrors.aliyun.com/pypi/simple/ --no-cache -e .

# 阶段2: 运行环境
FROM python:3.11-slim

WORKDIR /app

# 安装 curl（用于健康检查）
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 复制应用代码
COPY src/algomate ./algomate

# 创建数据目录
RUN mkdir -p /app/data

# 环境变量
ENV PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    DATABASE_URL=sqlite:///app/data/algomate.db

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "algomate.main:app", "--host", "0.0.0.0", "--port", "8000"]