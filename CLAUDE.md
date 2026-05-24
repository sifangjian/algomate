# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AlgoMate（算法修习助手）是一个 AI 驱动的游戏化算法学习应用。用户通过收集卡牌、与 NPC 导师对话、挑战 Boss 来学习算法，基于艾宾浩斯遗忘曲线实现间隔复习。

## Common Commands

### 开发环境启动
```bash
# 启动前后端（推荐）
python scripts/dev.py

# 仅后端（FastAPI，端口 8000）
python scripts/dev.py --backend

# 仅前端（Vite，端口 3000）
python scripts/dev.py --frontend

# 或直接用 uvicorn
uv run uvicorn algomate.main:app --reload
```

### 测试
```bash
# 运行全部后端测试
uv run pytest

# 运行单个测试文件
uv run pytest tests/test_boss_api.py

# 运行匹配名称的测试
uv run pytest tests/ -k "test_boss"

# 前端测试
cd frontend && npm test
```

### 依赖安装
```bash
uv sync                    # 后端依赖
cd frontend && npm install # 前端依赖
```

### 环境配置
```bash
cp .env.example .env       # 复制并填写 LLM_API_KEY
```

## Architecture

### 整体结构

前后端分离的单体应用：
- **Backend**: `src/algomate/` — Python FastAPI，端口 8000
- **Frontend**: `frontend/` — React + Vite，端口 3000
- **API 文档**: http://localhost:8000/docs（Swagger）

### 后端分层 (`src/algomate/`)

```
api/v1/          → FastAPI 路由（cards, npcs, bosses, dialogues, reviews 等）
models/          → SQLAlchemy ORM 模型（cards, bosses, npcs, battle_records 等）
data/repositories/ → 数据访问层（Repository 模式，每个实体一个 repo）
core/agent/      → AI Agent（ChatClient 包装 LangGraph，内容分析、题目生成、薄弱点分析）
core/flow/       → 业务流程编排（NPC 对话流、Boss 挑战流）
core/game/       → 游戏机制（耐久度、难度、境界解锁）
core/memory/     → 间隔复习算法（遗忘曲线引擎）
core/scheduler/  → 定时任务（复习调度、邮件通知）
config/          → 配置管理（AppConfig dataclass，支持 YAML + .env）
```

**入口**: `main.py` 中的 `AlgomateApp` 类初始化所有组件，`app` 变量（模块级）暴露 FastAPI 实例供 uvicorn 使用。

**路由统一**: 所有 API 路由统一使用 `/api/v1` 前缀，定义在 `api/v1/router.py` 中。

### 前端结构 (`frontend/src/`)

```
pages/           → 页面组件（HallPage, CardWorkshop, NpcDialogue, BossBattle, DailyReview, AdventureMap, Settings）
stores/          → Zustand 状态管理（每个领域一个 store）
services/        → API 调用封装（axios，对应后端各模块）
components/      → 可复用 UI 组件
hooks/           → 自定义 React hooks
```

### 数据库

SQLite（`data/algomate.db`），SQLAlchemy 2.0 ORM。测试使用内存 SQLite + `StaticPool`。

核心实体关系：NPC → Card/Boss（导师关联卡牌和 Boss），DialogueRecord → DialogueMessageRecord，BattleRecord 关联 Boss 和 Card。

### AI 层

使用 LangChain + LangGraph，默认模型为智谱 GLM-4。`ChatClient` 封装了 LangGraph 图，支持多轮对话状态管理。API Key 通过 `.env` 文件配置。

## Key Conventions

- 包管理：后端用 `uv`，前端用 `npm`
- Python 需要 type hints，变量命名 snake_case
- 测试框架：后端 pytest，前端 Vitest + Testing Library，E2E 用 Playwright
- git commit message 用中文，格式如 `feat(模块): 描述` 或 `fix(模块): 描述`
- 后端测试 fixture 在 `tests/conftest.py`，提供内存数据库和 mock FastAPI TestClient
- 卡牌系统有 10 个内容维度，Boss 题目由 AI 根据用户薄弱点生成
- 间隔复习间隔：1, 3, 7, 14, 30, 60 天
