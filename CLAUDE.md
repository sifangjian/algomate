# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AlgoMate（算法修习助手）** 是一个个人算法学习管理工具，通过卡牌系统 + 遗忘曲线复习来帮助用户系统化地学习算法。用户记录 LeetCode 题目的解法与技巧，由遗忘曲线引擎驱动定期复习，巩固记忆。

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
cd src && uv run uvicorn algomate.main:app --reload
```

### 测试
```bash
# 运行全部后端测试
uv run pytest

# 运行单个测试文件
uv run pytest tests/test_forgetting_curve_system.py

# 运行匹配名称的测试
uv run pytest tests/ -k "card"

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
cp .env.example .env       # 复制环境变量模板（无需额外配置）
```

## Architecture

### 整体结构

前后端分离的单体应用：
- **Backend**: `src/algomate/` — Python FastAPI，端口 8000
- **Frontend**: `frontend/` — React + Vite，端口 3000
- **API 文档**: http://localhost:8000/docs（Swagger）
- **数据库**: SQLite（`data/algomate.db`），SQLAlchemy 2.0 ORM

### 后端分层 (`src/algomate/`)

```
api/v1/               → FastAPI 路由
  ├── cards.py        → 通用卡牌 CRUD + 状态管理
  ├── problems.py     → 题目卡片（ProblemCard）CRUD
  ├── solutions.py    → 解法卡片（SolutionCard）CRUD + 关联技巧
  ├── techniques.py   → 技巧卡片（TechniqueCard）CRUD + 自评复习
  ├── reviews.py      → 修炼计划 V1
  ├── overview.py     → 主题聚合概览（首页网格）
  ├── dashboard.py    → 仪表盘 + 修炼操作
  ├── stats.py        → 统计
  ├── tasks.py        → 任务
  ├── progress.py     → 进度
  └── algorithm_info.py → 算法分类信息
models/               → SQLAlchemy ORM 模型
  ├── cards.py            → Card（遗忘曲线复习卡片，核心实体）
  ├── problem_card.py     → ProblemCard（LeetCode 题目索引）
  ├── solution_card.py    → SolutionCard（解法，关联题目与技巧）
  ├── technique_card.py   → TechniqueCard（原子化技巧，参与遗忘曲线）
  ├── solution_technique.py → 多对多关联表
  └── review_records.py   → ReviewRecord（修炼记录）
data/                 → 数据层
  ├── database.py         → Database 单例 + 自动迁移
  └── repositories/       → Repository 模式数据访问
core/                 → 核心业务逻辑
  ├── memory/
  │   ├── forgetting_curve.py  → 遗忘曲线引擎（间隔复习算法）
  │   ├── durability.py        → 耐久度管理（衰减/成功/失败）
  │   ├── difficulty.py        → 难度管理
  │   └── card_status.py       → 卡牌状态计算
  └── scheduler/
      └── review_scheduler.py  → APScheduler 定时修炼调度
review/               → 修炼计划服务
config/               → 配置管理
  ├── settings.py         → AppConfig dataclass（YAML + .env）
  └── algorithm_types.py  → 33 种算法分类体系 + 学习路径
utils/                → 工具函数
```

**入口**: `main.py` 中的 `AlgomateApp` 类初始化所有组件，`app` 变量（模块级）暴露 FastAPI 实例供 uvicorn 使用。

**路由统一**: 所有 API 路由统一使用 `/api/v1` 前缀，定义在 `api/v1/router.py` 中。

### 前端结构 (`frontend/src/`)

```
pages/              → 页面组件
  ├── HallPage.jsx              → 首页主题网格
  ├── TopicDetailPage.jsx       → 主题详情（题目/解法/技巧）
  ├── TechniqueListPage.jsx     → 技巧列表
  ├── CardDetailView.jsx        → 卡片详情（分屏查看）
  └── NotFound.jsx              → 404
components/         → 可复用组件
  ├── card/                     → 卡片相关（创建、编辑、详情、表单）
  ├── hall/                     → 首页组件（TopicGrid, HallHeader, etc.）
  ├── layout/                   → 布局（Header, SideNav, BottomNav）
  └── ui/                       → 通用 UI（Button, Modal, Toast, etc.）
stores/             → Zustand 状态管理（hallStore, cardStore, uiStore）
services/           → API 调用封装（axios）
hooks/              → 自定义 React hooks（useDebounce）
```

### 数据库核心实体关系

```
Card (遗忘曲线复习卡片)
  ├── TechniqueCard.card_id (1:1) — 技巧卡片，参与遗忘曲线复习
  └── ReviewRecord.card_id (1:N) — 修炼记录

ProblemCard (LeetCode 题目)
  └── SolutionCard.problem_id (1:N) — 解法

SolutionTechnique (多对多)
  ├── SolutionCard ←→ SolutionTechnique.solution_id
  └── TechniqueCard ←→ SolutionTechnique.technique_id
```

### 卡牌类型

| 类型 | 模型 | 参与遗忘曲线 | 说明 |
|------|------|-------------|------|
| 题目卡 | ProblemCard | 否 | LeetCode 题目索引，记录状态(untried/accepted/optimal) |
| 解法卡 | SolutionCard | 否 | 具体解法，包含复杂度、思路、代码、易错点 |
| 技巧卡 | TechniqueCard | 是 | 原子化算法技巧，自评驱动遗忘曲线复习 |

### 遗忘曲线复习机制

- 复习等级：0-6 级，间隔天数 [1, 3, 7, 14, 30, 60]
- 技巧卡自评复习：用户练习后自评（forgot/struggled/passed/mastered），系统根据自评调整间隔
- 耐久度系统：成功 +20，失败 -5，每日衰减 -2（3 天宽限期）
- 耐久度 < 30 为濒危，= 0 时需重修
- 复习调度器每日 9:00 自动生成修炼任务

### 算法分类体系

33 种算法类型，分为 10 大类别（基础数据结构、搜索、树、图、回溯、贪心、DP、分治排序、数学位运算），有完整的前置依赖关系和推荐学习路径。

## Key Conventions

- 包管理：后端用 `uv`，前端用 `npm`
- Python 需要 type hints，变量命名 snake_case
- 测试框架：后端 pytest，前端 Vitest + Testing Library
- git commit message 用中文，格式如 `feat(模块): 描述` 或 `fix(模块): 描述`
- 后端测试 fixture 在 `tests/conftest.py`，提供内存数据库和 mock FastAPI TestClient
- 前端 API 调用通过 `services/api.js`（axios 实例），统一错误处理 + 重试机制
- 创建技巧卡（TechniqueCard）时会同步创建 Card 复习记录
- 删除技巧卡时会同时删除关联的 Card 复习记录
- 题目卡和解法卡不参与遗忘曲线复习，仅技巧卡参与