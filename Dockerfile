# 后端 Dockerfile
# 使用多阶段构建优化镜像大小

# 阶段1: 构建依赖
FROM python:3.11-slim AS builder

# 配置国内镜像源加速
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# 复制依赖文件
COPY pyproject.toml ./

# 安装依赖到虚拟环境（使用清华 PyPI 镜像）
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv pip install --no-cache -i https://pypi.tuna.tsinghua.edu.cn/simple -e .

# 阶段2: 运行环境
FROM python:3.11-slim

WORKDIR /app

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