# AlgoMate 算法学习助手

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)  [![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)](https://doc.qt.io/qtforpython/)  [![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*基于 AI Agent 的个人算法学习助手 - 用智能对抗遗忘曲线*

[English](./README.md) | 简体中文

</div>

---

## 📖 项目介绍

在算法学习过程中，你是否也面临"前学后忘"的困扰？随着时间推移，知识点逐渐模糊，需要一个智能化的学习助手来帮助你整理、巩固和强化学习成果。

**AlgoMate** 是一款基于 AI Agent 的个人算法学习助手，核心目标是帮助用户对抗遗忘曲线，通过**笔记整理**、**定期复习**、**智能出题**等方式，将零散的算法知识逐步构建成系统化的个人知识体系。

### 🎯 核心价值

- **🧠 智能整理** - AI 自动解析和分类你的算法笔记
- **📚 对抗遗忘** - 基于艾宾浩斯遗忘曲线理论的科学复习计划
- **🎯 精准出击** - 通过智能出题测试，精准定位薄弱点
- **📊 可视化进度** - 游戏化进度展示，增强学习动力

---

## ✨ 功能特性

### 核心功能

| 功能             | 描述                                          |
| ---------------- | --------------------------------------------- |
| 📝 **笔记管理**   | 支持 Markdown 格式输入/粘贴，自动解析存储     |
| 🏷️ **智能归类**   | AI 自动按算法类型分类（DFS、BFS、动态规划等） |
| 📧 **复习提醒**   | 基于遗忘曲线定时邮件推送复习内容              |
| 🤖 **智能出题**   | 根据薄弱点生成针对性练习题（选择/简答/代码）  |
| 📈 **薄弱点分析** | 基于答题情况自动分析薄弱知识点                |
| 🎮 **进度可视化** | 雷达图展示各算法类型掌握程度                  |

### 题目类型支持

- **选择题** - 概念题、特点题、时间复杂度分析
- **简答题** - 算法思路解释、复杂度分析、边界条件讨论
- **代码题** - 代码补全、输出预测、Bug 查找

---

## 🛠️ 技术栈

| 组件        | 技术选型             | 说明               |
| ----------- | -------------------- | ------------------ |
| 🐍 开发语言  | Python 3.10+         | 用户偏好           |
| � 包管理    | uv                   | 现代 Python 包管理 |
| �🖥️ GUI 框架 | PyQt5 / PySide6      | 跨平台桌面应用     |
| 💾 数据库    | SQLite + SQLAlchemy  | 本地存储，ORM 操作 |
| 🤖 AI 模型   | 智谱 GLM-4 (ChatGLM) | Agent 核心能力     |
| 📧 邮件服务  | smtplib              | 复习提醒           |
| ⏰ 定时任务  | APScheduler          | 定时发送邮件       |
| 📄 配置管理  | PyYAML               | 本地配置文件       |

---

## 📁 项目结构

```
algomate/
├── main.py                      # 应用入口
├── config/
│   ├── settings.py              # 配置管理
│   └── algorithm_types.py       # 算法分类配置
├── core/
│   ├── agent/                   # AI Agent 核心
│   │   ├── chat_client.py       # GLM API 调用封装
│   │   ├── note_analyzer.py     # 笔记理解与分析
│   │   ├── question_generator.py# 题目生成器
│   │   └── weak_point_analyzer.py# 薄弱点分析
│   ├── scheduler/               # 调度器
│   │   ├── review_scheduler.py  # 复习计划调度
│   │   └── email_sender.py      # 邮件发送器
│   └── memory/
│       └── forgotten_curve.py   # 遗忘曲线算法
├── data/
│   ├── database.py              # 数据库连接与初始化
│   ├── models.py                # 数据模型
│   └── repositories/            # 数据仓库层
├── ui/
│   ├── main_window.py           # 主窗口
│   ├── pages/                   # 页面模块
│   │   ├── dashboard.py         # 首页/仪表盘
│   │   ├── note_manager.py      # 笔记管理
│   │   ├── practice_center.py   # 练习中心
│   │   ├── progress_view.py     # 进度可视化
│   │   └── settings_page.py     # 个人设置
│   └── components/               # UI 组件
└── tests/                       # 单元测试
```

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) - 现代 Python 包管理器
- PyQt5 5.15+

### 安装步骤

```bash
# 克隆项目
git clone git@github.com:sifangjian/algomate.git
cd algomate

# 使用 uv 创建虚拟环境并安装依赖
uv venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate   # Windows

uv pip install -r requirements.txt

# 运行应用
python main.py
```

### 配置说明

首次运行后，配置文件位于 `~/.algorithm_assistant/config.yaml`，需要配置以下内容：

```yaml
# AI 配置
zhipu_api_key: "your_api_key_here"
zhipu_model: "glm-4"

# 邮件配置（用于复习提醒）
smtp_host: "smtp.qq.com"
smtp_port: 465
smtp_user: "your_email@qq.com"
smtp_password: "your授权码"
email_to: "your_email@qq.com"

# 复习提醒配置
review_time: "09:00"
review_enabled: true
```

---

## 🔬 核心模块设计

### 遗忘曲线算法

基于艾宾浩斯遗忘曲线理论，复习节点设置为：

```
复习周期: 1天 → 3天 → 7天 → 14天 → 30天 → 60天
```

当用户学习新笔记后，系统会自动创建复习任务，在指定时间提醒用户复习，并通过邮件发送复习内容。

### AI Agent 能力

| 能力       | 说明                             |
| ---------- | -------------------------------- |
| 📖 笔记理解 | 理解笔记内容，提取关键知识点     |
| 🏷️ 智能分类 | 判断笔记应属的算法类型和标签     |
| 📝 题目生成 | 根据薄弱点生成针对性练习题       |
| ✅ 答题评判 | 分析用户答案，给出评价和改进建议 |
| 📅 学习规划 | 根据用户情况制定复习计划         |

---

## 📊 学习进度可视化

- **雷达图** - 展示各算法类型的掌握程度
- **进度条** - 展示整体学习进度
- **遗忘曲线图** - 可视化记忆保持情况
- **等级系统** - 游戏化学习激励机制

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

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [智谱 AI](https://www.zhipuai.cn/) - 提供 GLM-4 大模型支持
- [PyQt5](https://doc.qt.io/qtforpython/) - 强大的 GUI 框架
- 所有开源贡献者

---

<div align="center">

**如果这个项目对你有帮助，欢迎 ⭐ Star！**

Made with ❤️ by [sifangjian](https://github.com/sifangjian)

</div>
