# AlgoMate 算法大陆

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**在算法大陆的冒险中，成为算法大师**

</div>

***

## 项目概述

**AlgoMate 算法大陆** 是一款基于 AI Agent 的游戏化算法修习助手，帮助用户对抗遗忘曲线，真正掌握算法技巧并熟练用于实战。

### 核心价值

- 🎮 **游戏化修习**：卡牌收集、Boss 挑战、等级成长让修习不再枯燥
- 🧠 **对抗遗忘**：基于艾宾浩斯遗忘曲线理论的科学修炼机制
- 🤖 **AI 导师**：通过对话问答修习算法技巧
- ⚔️ **个性化出题**：AI 根据你的薄弱点针对性生成 Boss

***

## 核心功能

AlgoMate 包含 **4 大功能模块**，形成完整的学习闭环：

### F01 卡牌系统 🎴

卡牌是算法技巧的完整知识载体，包含 10 个内容维度：核心概念、要点列表、代码模板、复杂度分析、适用场景、常见变体、典型题目、常见坑点、对比辨析、我的心得。

### F02 NPC 对话修习 🤖

与 8 位领域专家 NPC 进行气泡式对话，学习特定算法技巧，对话结束后 AI 自动生成卡牌。

### F03 Boss 挑战 ⚔️

挑战 Boss 完成算法试炼，包含选择题、简答题、LeetCode 挑战三种题型，击败 Boss 可提升卡牌耐久度。

### F04 遗忘曲线修炼 📧

基于艾宾浩斯遗忘曲线，系统自动生成每日修炼任务，修炼节点：1天、3天、7天、14天、30天、60天。

***

## 安装与配置

### 环境要求

- Node.js 18+
- uv（Python 包管理器）
- pnpm（Node.js 包管理器）

### 安装步骤

```bash
# 1. 克隆项目
git clone git@github.com:sifangjian/algomate.git
cd algomate

# 2. 安装后端依赖
uv sync

# 3. 安装前端依赖
cd frontend && npm install && cd ..

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 LLM_API_KEY（智谱 API 密钥）
```

### 配置说明

**必填配置**：

| 变量名           | 说明              | 获取方式                              |
| ------------- | --------------- | --------------------------------- |
| `LLM_API_KEY` | 智谱 GLM-4 API 密钥 | 访问 <https://open.bigmodel.cn/> 获取 |

**可选配置**：

| 变量名              | 默认值                          | 说明           |
| ---------------- | ---------------------------- | ------------ |
| `APP_ENV`        | `development`                | 运行环境         |
| `DATABASE_URL`   | `sqlite:///data/algomate.db` | 数据库路径        |
| `ENCRYPTION_KEY` | 无                            | AES-256 加密密钥 |

***

## 使用方法

### 启动应用

**开发环境**：

```bash
# 终端 1：启动后端
uv run uvicorn algomate.main:app --reload

# 终端 2：启动前端
cd frontend && pnpm dev
```

访问：<http://localhost:3000>

**生产环境**：

```bash
# 构建前端
cd frontend && pnpm build && cd ..

# 启动后端
export APP_ENV=production
uv run uvicorn algomate.main:app --host 0.0.0.0 --port 8000
```

访问：<http://localhost:8000>

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

***

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: 添加某个新功能'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request


***

## 许可证

本项目基于 [MIT 许可证](LICENSE) 开源。

***

## 联系方式

- **问题反馈**：[GitHub Issues](https://github.com/sifangjian/algomate/issues)
- **讨论交流**：[GitHub Discussions](https://github.com/sifangjian/algomate/discussions)

***

## 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代、快速的 Web 框架
- [React](https://react.dev/) - 用于构建用户界面的 JavaScript 库
- [LangChain](https://www.langchain.com/) - LLM 应用开发框架
- [智谱 AI](https://www.bigmodel.cn/) - 提供 GLM-4 API

***

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐️ Star 支持一下！**

Made with ❤️ by AlgoMate Team

</div>
