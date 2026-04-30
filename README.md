# AlgoMate 算法大陆

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*在算法大陆的冒险中，成为算法大师*

</div>

---

## 📖 项目介绍

算法修习是一个长期的、枯燥的过程，容易中途放弃、前学后忘。你是否也面临这样的困扰？

**AlgoMate 算法大陆** 是一款基于 AI Agent 的游戏化算法修习助手。它将算法修习转化为一场冒险旅程——你在「算法大陆」上收集卡牌、挑战 Boss、对抗遗忘，最终成为领悟算法技巧的冒险者。

### 🎯 核心价值

- **🎮 游戏化修习**: 卡牌收集、Boss 挑战、等级成长让修习不再枯燥
- **🧠 对抗遗忘**: 基于艾宾浩斯遗忘曲线理论的科学修炼机制
- **🤖 AI 导师**: 通过对话问答修习算法技巧，AI 自动分析产出卡牌
- **⚔️ 个性化出题**: AI 根据你的薄弱点针对性生成 Boss

### 📖 Slogan

**在算法大陆的冒险中，成为算法大师**

---

## ✨ 功能特性

### 🎴 卡牌系统

- 每张卡牌代表一个独立的算法技巧（「二分查找」「滑动窗口」「DFS」等）
- 卡牌有耐久度属性，长期不修炼会降低，修炼或击败 Boss 会提升
- 通过 NPC 对话修习或击败 Boss 掉落获得新卡牌

### 🤖 NPC 对话系统

- 与领域专家 NPC 进行气泡 UI 问答修习
- 对话结束后自动生成对应卡牌
- 8 位领域专家 NPC：老夫子、树语者、沼泽向导、圣殿智者、贪婪之王、迷宫守护者、分裂贤者、数学巫师

### ⚔️ Boss 挑战系统

- 选择卡牌应战 Boss，完成算法试炼
- 系统根据你的已有卡牌生成个性化 Boss
- 击败 Boss 有概率掉落新卡牌

### 🔓 秘境解锁系统

- 算法大陆由 8 个秘境组成，不会一次性开放
- 通过"精通度达标卡牌数量"解锁新秘境和新 NPC
- 满足条件后新秘境逐渐"点亮"

### 📧 遗忘曲线修炼

- 基于艾宾浩斯遗忘曲线生成修炼任务
- 优先推送濒危卡牌（耐久度 < 30）
- 支持邮件提醒，利用碎片时间修炼

### 🎚️ 游戏难度设置

| 难度 | 耐久度变化 | Boss 掉卡率 | 每日任务 |
| ---- | ---------- | ----------- | -------- |
| 简单 | 降低 50%   | +15%        | 3 个     |
| 普通 | 标准       | 标准        | 5 个     |
| 困难 | 增加 50%   | +30%        | 8 个     |

---

## 🛠️ 技术栈

| 组件       | 技术选型              | 说明                     |
| ---------- | --------------------- | ------------------------ |
| 🐍 开发语言 | Python 3.10+          | 后端服务                 |
| ⚛️ 前端框架 | React 18 + Ant Design | 网页端更好的交互体验     |
| 🚀 后端框架 | FastAPI               | Python 生态，AI 集成方便 |
| 💾 数据库   | SQLite + SQLAlchemy   | 本地存储                 |
| 🤖 AI 模型  | 智谱 GLM-4            | Agent 核心能力           |
| 📧 邮件服务 | SMTP                  | 修炼提醒                 |
| ⏰ 定时任务 | APScheduler           | 定时推送                 |

---

## 📁 项目结构

```
algomate/
├── src/
│   └── algomate/
│       ├── main.py              # FastAPI 应用入口
│       ├── config/
│       │   └── settings.py      # 配置管理
│       ├── core/
│       │   ├── agent/           # AI Agent 核心
│       │   │   ├── chat_client.py       # GLM API 调用
│       │   │   ├── dialogue_manager.py  # NPC 对话管理
│       │   │   ├── card_generator.py    # 卡牌生成器
│       │   │   └── boss_generator.py    # Boss 生成器
│       │   ├── scheduler/       # 调度器
│       │   │   ├── review_scheduler.py  # 修炼计划调度
│       │   │   └── email_sender.py      # 邮件发送器
│       │   └── memory/
│       │       └── forgotten_curve.py   # 遗忘曲线算法
│       ├── data/
│       │   ├── database.py      # 数据库连接
│       │   ├── models.py        # 数据模型
│       │   └── repositories/    # 数据仓库层
│       └── api/
│           ├── routes/          # API 路由
│           └── schemas/          # Pydantic 模型
├── frontend/                    # React 前端项目
│   ├── src/
│   │   ├── pages/               # 页面组件
│   │   ├── components/         # 公共组件
│   │   ├── hooks/               # 自定义 Hooks
│   │   └── services/            # API 调用
│   └── package.json
└── docs/                        # 设计文档
    ├── 产品设计.md
    └── 需求分析.md
```

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- [uv](https://github.com/astral-sh/uv) - Python 包管理器
- [pnpm](https://pnpm.io/) - Node.js 包管理器

### 安装步骤

```bash
# 克隆项目
git clone git@github.com:sifangjian/algomate.git
cd algomate

# 后端安装
cd src
uv venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate   # Windows
uv pip install -r requirements.txt

# 前端安装
cd frontend
pnpm install

# 配置
# 复制并编辑配置文件
cp src/algomate/config.example.yaml src/algomate/config.yaml
```

### 配置说明

配置文件位于 `src/algomate/config.yaml`：

```yaml
# AI 配置
zhipu_api_key: "your_api_key_here"
zhipu_model: "glm-4"

# 邮件配置（用于修炼提醒）
smtp_host: "smtp.qq.com"
smtp_port: 465
smtp_user: "your_email@qq.com"
smtp_password: "your授权码"

# 游戏设置
game_difficulty: "normal"  # easy / normal / hard
daily_review_time: "09:00"
```

### 运行应用

```bash
# 启动后端
cd src
uvicorn algomate.main:app --reload

# 启动前端（新终端）
cd frontend
pnpm dev
```

访问 `http://localhost:3000` 即可开始冒险！

---

## 🎮 核心机制

### 遗忘曲线算法

基于艾宾浩斯遗忘曲线，修炼节点设置为：

```
创建卡片 → 1天后 → 3天后 → 7天后 → 14天后 → 30天后 → 60天后
```

### 卡牌耐久度规则

| 行为           | 耐久度变化                |
| -------------- | ------------------------- |
| 初始创建       | 80                        |
| 修炼/击败 Boss | min(100, 耐久度 + 20)     |
| 未击败 Boss    | max(0, 耐久度 - 5)        |
| 未修炼（每天） | max(0, 耐久度 - 2)        |
| 濒危阈值       | 耐久度 < 30               |
| 卡牌消散       | 耐久度 = 0 时进入封印状态 |

### 秘境解锁规则

| 秘境     | 解锁条件                      |
| -------- | ----------------------------- |
| 新手森林 | 默认解锁                      |
| 迷雾沼泽 | 新手森林精通度≥60的卡牌 ≥ 3张 |
| 智慧圣殿 | 迷雾沼泽精通度≥60的卡牌 ≥ 3张 |
| ...      | ...                           |

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 📄 许可证

本项目基于 MIT 许可证开源。
