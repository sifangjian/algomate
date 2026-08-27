# 部署与开发指南

本文档包含 AlgoMate 的详细部署、开发和配置说明。

***

## 环境要求

- Docker 与 Docker Compose（推荐部署方式）
- 或：Python 3.11+、Node.js 18+、uv、npm

***

## 快速开始（Docker Compose，推荐）

```bash
# 1. 克隆项目
git clone git@github.com:sifangjian/algomate-helper.git
cd algomate-helper

# 2. 配置环境变量（默认无需额外配置，前后端端口保持默认即可）
cp .env.example .env

# 3. 构建并启动全部服务
docker compose up --build -d

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

Docker Compose 会构建两个镜像并启动两个服务：
- `backend`：FastAPI 后端（容器内端口 8000，默认映射到宿主机 8000，受 `.env` 的 `BACKEND_PORT` 控制）
- `frontend`：Vite 开发服务器（端口 3000，带热更新）

访问：
- 前端：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs（Swagger UI）

按 `Ctrl+C` 或 `docker compose down` 停止服务。

***

## 手动部署（不使用 Docker）

```bash
# 1. 安装依赖
uv sync
cd frontend && npm install && cd ..

# 2. 配置环境变量
cp .env.example .env

# 3. 构建前端
cd frontend && npm run build && cd ..

# 4. 启动后端
cd src && uv run uvicorn algomate.main:app --host 0.0.0.0 --port 8000
```

访问：http://localhost:8000（前端静态文件由后端提供服务）

**停止服务**：
```bash
lsof -i :8000    # 查找进程
kill <PID>       # 终止进程
```

***

## 本地开发（不使用 Docker）

```bash
# 安装依赖
uv sync
cd frontend && npm install && cd ..

# 配置环境变量
cp .env.example .env

# 同时启动前后端（Vite + FastAPI）
python scripts/dev.py
# 仅后端：python scripts/dev.py --backend
# 仅前端：python scripts/dev.py --frontend
```

访问：
- 前端：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

***

## 镜像构建说明

两个 Dockerfile 均内置了国内镜像源以加速构建：
- 后端 `Dockerfile`：使用清华 PyPI 镜像（`pypi.tuna.tsinghua.edu.cn`）
- 前端 `frontend/Dockerfile`：使用 npmmirror 淘宝镜像（`registry.npmmirror.com`）

> 注意：`frontend/package-lock.json` 中所有包的下载地址必须指向可访问的镜像（当前为 `registry.npmmirror.com`）。若曾在内网环境（如腾讯云）生成锁文件，其中可能混入了内网域名（如 `mirrors.tencentyun.com`），本地或 Docker 构建会解析失败，需将其替换为 `registry.npmmirror.com` 上的同版本地址后再构建。

构建命令：
```bash
# 构建两个镜像
docker compose build

# 仅构建后端 / 前端
docker compose build backend
docker compose build frontend

# 构建并启动
docker compose up --build -d
```

***

## 项目结构

```
algomate-helper/
├── src/algomate/          # 后端源代码
│   ├── main.py            # 应用入口（AlgomateApp 类）
│   ├── api/v1/            # API 路由（cards, problems, solutions, techniques, reviews, activity-logs 等）
│   ├── models/            # SQLAlchemy ORM 模型（含 activity_log 活动日志）
│   ├── core/              # 核心业务逻辑（遗忘曲线、耐久度、调度器）
│   ├── review/            # 修炼计划服务
│   ├── config/            # 配置管理（AppConfig + 算法分类）
│   ├── data/              # 数据层（Database 单例 + Repository）
│   └── utils/             # 工具函数
├── frontend/              # 前端源代码（React + Vite）
│   └── src/
│       ├── pages/         # 页面组件
│       ├── components/    # UI 组件
│       ├── stores/        # Zustand 状态管理
│       ├── services/      # API 调用封装
│       └── hooks/         # 自定义 React hooks
├── tests/                 # 后端测试
├── data/                  # 数据目录（SQLite 数据库 + 配置文件）
├── logs/                  # 日志目录
├── scripts/               # 开发工具脚本
├── .env.example           # 环境变量示例
├── pyproject.toml         # Python 项目配置
├── Dockerfile             # 后端 Docker 构建
└── docker-compose.yml     # Docker Compose 配置
```

***

## 配置说明

### 环境变量 (`.env`)

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `FRONTEND_PORT` | 3000 | 前端开发服务器端口 |
| `BACKEND_PORT` | 8000 | 后端宿主机映射端口（compose 中映射到容器 8000） |
| `VITE_API_URL` | http://localhost:8000 | 前端 API 代理目标地址 |

### 配置文件 (`data/config.yaml`)

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `APP_NAME` | 算法修习助手 | 应用名称 |
| `VERSION` | 0.1.0 | 应用版本 |
| `DATA_DIR` | ./data | 数据存储目录 |
| `DB_PATH` | ./data/algomate.db | SQLite 数据库路径 |
| `LOG_PATH` | ./logs/algomate.log | 日志文件路径 |
| `REVIEW_INTERVALS` | [1,3,7,14,30,60] | 遗忘曲线复习间隔（天） |
| `REVIEW_TIME` | 09:00 | 每日自动生成修炼任务的时间（APScheduler） |

***

## 测试

```bash
# 后端测试（使用已启动的容器）
docker compose exec backend uv run pytest
docker compose exec backend uv run pytest tests/ -k "card"
docker compose exec backend uv run pytest tests/test_forgetting_curve_system.py

# 前端测试
docker compose exec frontend npm test
docker compose exec frontend npm run test:watch   # 监听模式
```

当前后端测试文件：
- `tests/test_db_init.py`
- `tests/test_f04_review_records.py`
- `tests/test_forgetting_curve_system.py`
- `tests/test_review_statistics.py`

测试 fixture 位于 `tests/conftest.py`（提供内存数据库与 mock FastAPI TestClient）。

***

## 常见问题

### 数据库文件在哪？

默认位于 `data/algomate.db`。删除该文件后重新启动应用会自动创建新的数据库。

### 如何重置数据？

删除 `data/algomate.db` 文件即可。应用启动时会自动创建表结构。

### 前端开发时跨域问题？

Vite 开发服务器已配置 `/api` 代理到后端（`http://localhost:8000`），无需额外配置。

### 日志文件在哪？

默认位于 `logs/algomate.log`，包含应用运行日志和错误信息。
