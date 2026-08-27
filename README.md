# AlgoMate 算法修习助手

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**个人算法学习管理工具 — 题解记录 + 遗忘曲线复习**

</div>

***

## 项目概述

**AlgoMate** 是一款面向算法学习者的个人管理工具，帮助你系统化地记录 LeetCode 题解、沉淀算法技巧，并通过基于艾宾浩斯遗忘曲线的间隔复习机制巩固记忆。

### 核心价值

- **系统化记录**：题解、解法、技巧三层结构，知识体系清晰可追溯
- **对抗遗忘**：基于艾宾浩斯遗忘曲线的自评复习，科学安排复习节奏
- **知识关联**：解法与技巧多对多关联，构建算法知识网络
- **自主掌控**：自评驱动复习计划，灵活适配个人学习节奏
- **活动日志**：自动与手动记录学习轨迹（创建、查看、更新卡片及笔记），方便回顾当日/阶段进展

***

## 功能特性

### 卡牌系统

三种类型的卡牌构成完整的学习闭环：

| 卡牌类型 | 说明 | 参与遗忘曲线 |
|---------|------|------------|
| **题目卡** | LeetCode 题目索引，记录题目状态（未做/通过/最优） | 否 |
| **解法卡** | 具体解法，包含复杂度、突破口、思路、代码、易错点 | 否 |
| **技巧卡** | 原子化算法技巧，沉淀可复用的解题模式 | **是** |

### 主题网格

首页按 33 种算法类型组织展示，每种类型统计题目数、解法数、技巧数，以及待复习和濒危技巧数量，一目了然掌握学习进度。

### 主题详情

进入具体算法类型，分栏展示关联的题目、解法、技巧卡片，支持分屏查看关联卡片详情。

### 遗忘曲线复习

仅技巧卡参与遗忘曲线复习，间隔天数遵循 `[1, 3, 7, 14, 30, 60]` 天：
- 用户自评四个等级：**忘了 / 吃力 / 通过 / 精通**
- 系统根据自评动态调整耐久度和下次复习间隔
- 耐久度系统：成功 +20，失败 -5，每日衰减 -2
- 耐久度低于 30 标记为濒危，归零时需重修

### 耐久度机制

每张卡牌拥有耐久度（0-100），反映对该知识的掌握程度：
- **修炼成功**：耐久度 +20
- **修炼失败**：耐久度 -5
- **每日衰减**：耐久度 -2（创建后 3 天宽限期）
- **濒危状态**：耐久度 < 30
- **重修状态**：耐久度 = 0，需通过重修恢复

### 算法分类体系

内置 33 种算法类型，按 10 大类别组织（基础数据结构、搜索、树、图、回溯、贪心、DP、分治排序、数学位运算），包含完整的前置依赖关系和推荐学习路径。

### 活动日志

系统自动记录学习行为（创建/查看/更新卡片），也支持手动添加笔记。可在前端「活动」相关视图按日期、类型筛选回顾，便于追踪学习轨迹。

***

## 快速开始

### 环境要求

- Docker 与 Docker Compose（推荐，免去本地装 Python/Node）
- 或：Python 3.11+、Node.js 18+、uv、npm

### 方式一：Docker Compose 一键启动（推荐）

```bash
# 1. 克隆项目
git clone git@github.com:sifangjian/algomate-helper.git
cd algomate-helper

# 2. 配置环境变量（默认无需额外配置）
cp .env.example .env

# 3. 构建并启动全部服务（前端 + 后端）
docker compose up --build -d

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

访问：
- 前端：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

> 后端端口默认映射到宿主机 8000（见 `docker-compose.yml` 的 `BACKEND_PORT`），方便本地直接访问 API 文档与调试。

### 方式二：本地开发（不使用 Docker）

```bash
# 1. 安装依赖
uv sync
cd frontend && npm install && cd ..

# 2. 配置环境变量
cp .env.example .env

# 3. 启动开发服务器（前后端同时启动）
python scripts/dev.py
```

访问：
- 前端：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

***

## 技术栈

### 后端

| 技术 | 用途 |
|------|------|
| Python 3.11+ | 编程语言 |
| FastAPI | Web 框架 |
| SQLAlchemy 2.0 | ORM |
| SQLite | 数据库 |
| APScheduler | 定时任务调度（每日 09:00 生成修炼任务） |
| PyYAML | 配置管理 |

### 前端

| 技术 | 用途 |
|------|------|
| React 18 | UI 框架 |
| Vite | 构建工具 |
| React Router | 路由 |
| Zustand | 状态管理 |
| Axios | HTTP 客户端 |
| CodeMirror | 代码编辑器 |
| react-markdown | Markdown 渲染 |
| react-force-graph-2d | 知识关联图可视化 |

***

## 项目结构

```
algomate-helper/
├── src/algomate/          # 后端源代码
│   ├── main.py            # 应用入口 + FastAPI 实例（AlgomateApp 类）
│   ├── api/v1/            # RESTful API 路由
│   ├── models/            # 数据模型（含 activity_log 活动日志）
│   ├── core/              # 核心逻辑（遗忘曲线、耐久度、调度）
│   ├── review/            # 修炼计划服务
│   ├── config/            # 配置管理（AppConfig + 算法分类）
│   ├── data/              # 数据层（Database 单例 + Repository）
│   └── utils/             # 工具函数
├── frontend/              # 前端源代码
│   └── src/
│       ├── pages/         # 页面（首页/题目/解法/技巧/复习/主题详情）
│       ├── components/     # 组件（card/hall/layout/ui 等）
│       ├── stores/         # 状态管理（cardStore/hallStore/uiStore）
│       ├── services/       # API 服务（axios 封装）
│       ├── hooks/          # 自定义 Hooks
│       └── constants/      # 常量
├── tests/                 # 后端测试
├── data/                  # 数据库 + 配置文件
├── scripts/               # 开发工具脚本（dev.py 统一启动）
├── Dockerfile             # 后端 Docker 构建
├── docker-compose.yml     # Docker Compose 配置（backend + frontend）
└── .env.example           # 环境变量示例
```

***

## 许可证

本项目基于 [MIT 许可证](LICENSE) 开源。

***

## 联系方式

- **问题反馈**：[GitHub Issues](https://github.com/sifangjian/algomate-helper/issues)
- **讨论交流**：[GitHub Discussions](https://github.com/sifangjian/algomate-helper/discussions)
