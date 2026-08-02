# 部署与开发指南

本文档包含 AlgoMate 的详细部署、开发和配置说明。

***

## 环境要求

- Python 3.11+
- Node.js 18+
- uv（Python 包管理器）
- npm（随 Node.js 安装）

***

## 快速开始（开发环境）

```bash
# 1. 克隆项目
git clone git@github.com:sifangjian/algomate.git
cd algomate

# 2. 安装依赖
uv sync
cd frontend && npm install && cd ..

# 3. 配置环境变量
cp .env.example .env
# .env 文件默认无需额外配置，前后端端口保持默认即可

# 4. 启动开发服务器（前后端同时启动）
python scripts/dev.py
```

访问：
- 前端：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs（Swagger UI）

按 `Ctrl+C` 停止服务。

***

## 手动部署（生产环境）

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

## Docker 部署

### 后端 Docker

```bash
# 构建镜像
docker build -t algomate-backend .

# 运行容器
docker run -d \
  --name algomate-backend \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  algomate-backend
```

### 开发环境（Docker Compose）

```bash
# 启动全部服务
docker compose up -d

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

Docker Compose 会启动两个服务：
- `backend`: FastAPI 后端（端口 8000）
- `frontend`: Vite 开发服务器（端口 3000，带热更新）

***

## 项目结构

```
algomate/
├── src/algomate/          # 后端源代码
│   ├── main.py            # FastAPI 应用入口（AlgomateApp 类）
│   ├── api/v1/            # API 路由（cards, problems, solutions, techniques 等）
│   ├── models/            # SQLAlchemy ORM 模型
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

***

## 测试

```bash
# 后端测试
uv run pytest                          # 全部测试
uv run pytest tests/ -k "card"         # 按名称匹配
uv run pytest tests/test_f01_card_system.py  # 单个文件

# 前端测试
cd frontend && npm test                # 全部测试
cd frontend && npm run test:watch      # 监听模式
```

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