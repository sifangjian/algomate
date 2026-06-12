# 部署与开发指南

本文档包含 AlgoMate 的详细部署、开发和配置说明。

***

## 手动部署

**环境要求**：Python 3.11+、Node.js 18+、uv

```bash
# 1. 克隆项目
git clone git@github.com:sifangjian/algomate.git
cd algomate

# 2. 安装依赖
uv sync
cd frontend && npm install && cd ..

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 LLM_API_KEY

# 4. 构建前端
cd frontend && npm run build && cd ..

# 5. 启动后端
export APP_ENV=production
uv run uvicorn algomate.main:app --host 0.0.0.0 --port 8000
```

访问：<http://localhost:8000>

**停止服务**：

```bash
lsof -i :8000    # 查找进程
kill <PID>       # 终止进程
```

***

## 开发调试

```bash
# 安装依赖
uv sync && cd frontend && npm install && cd ..

# 配置环境变量
cp .env.example .env

# 启动开发服务器（前后端同时启动）
python scripts/dev.py

# 或单独启动
python scripts/dev.py --backend   # 仅后端
python scripts/dev.py --frontend  # 仅前端
```

按 `Ctrl+C` 停止服务。

***

## 配置说明

**必填配置**：

| 变量名          | 说明               | 获取方式                              |
| --------------- | ------------------ | ------------------------------------- |
| `LLM_API_KEY`   | 智谱 GLM-4 API 密钥 | 访问 <https://open.bigmodel.cn/> 获取 |

**可选配置**：

| 变量名            | 默认值                      | 说明           |
| ----------------- | --------------------------- | -------------- |
| `APP_ENV`         | `development`               | 运行环境       |
| `DATABASE_URL`    | `sqlite:///data/algomate.db` | 数据库路径     |
| `ENCRYPTION_KEY`  | 无                          | AES-256 加密密钥 |

***

## 项目结构

```
algomate/
├── src/algomate/          # 后端源代码
│   ├── main.py            # FastAPI 应用入口
│   ├── api/               # API 层
│   ├── core/              # 核心层（AI Agent、游戏机制、遗忘曲线）
│   ├── data/              # 数据层
│   └── models/            # 数据模型
├── frontend/              # 前端源代码
│   └── src/
│       ├── pages/         # 页面组件
│       ├── components/    # UI 组件
│       ├── stores/        # 状态管理
│       └── services/      # API 服务
├── tests/                 # 测试文件
├── .trae/specs/           # 项目文档
├── .env.example           # 环境变量示例
└── pyproject.toml         # Python 项目配置
```
