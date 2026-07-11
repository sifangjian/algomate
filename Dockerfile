# 阶段1: 构建依赖
FROM python:3.11-slim AS builder

WORKDIR /app

# 只复制依赖定义文件，不复制项目代码（镜像不包含代码）
COPY pyproject.toml uv.lock README.md ./

ENV UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple uv && \
    uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv sync --active --no-install-project --frozen

# 阶段2: 运行环境
FROM python:3.11-slim

WORKDIR /app

# 虚拟环境放在/opt/venv，不会被volume挂载覆盖
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN mkdir -p /app/data

ENV PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    DATABASE_URL=sqlite:///app/data/algomate.db \
    PYTHONPATH=/app/src

EXPOSE 8000

CMD ["uvicorn", "algomate.main:app", "--host", "0.0.0.0", "--port", "8000"]
