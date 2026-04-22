"""
Algomate 主程序模块

算法学习助手主程序入口，负责：
- 应用初始化和配置
- AI 组件的初始化
- 复习调度器的启动和管理
- 日志系统配置

Usage:
    from src.algomate.main import AlgomateApp

    app = AlgomateApp()
    app.start_review_scheduler()
"""

import logging
import sys
from pathlib import Path

from algomate.config.settings import AppConfig
from .data.database import Database
from .core.agent.chat_client import ChatClient
from .core.agent.note_analyzer import NoteAnalyzer
from .core.agent.question_generator import QuestionGenerator
from .core.agent.weak_point_analyzer import WeakPointAnalyzer
from .core.memory.forgotten_curve import ForgottenCurve
from .core.scheduler.review_scheduler import ReviewScheduler
from .core.scheduler.email_sender import EmailSender

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def setup_logging(config: AppConfig):
    """配置日志系统

    设置日志输出到控制台和文件。

    Args:
        config: 应用配置
    """
    log_file = config.LOG_PATH
    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logging.getLogger().addHandler(file_handler)


class AlgomateApp:
    """算法学习助手应用类

    应用主类，负责整体组件的初始化和管理。

    Attributes:
        config: 应用配置
        db: 数据库实例
        chat_client: AI 对话客户端
        note_analyzer: 笔记分析器
        question_generator: 题目生成器
        weak_point_analyzer: 薄弱点分析器
        forgotten_curve: 遗忘曲线算法
        review_scheduler: 复习调度器
    """

    def __init__(self, config: AppConfig = None):
        """初始化应用

        Args:
            config: 应用配置，默认从配置文件加载
        """
        self.config = config or AppConfig.load()
        setup_logging(self.config)
        self.db = Database.get_instance(self.config)
        self.chat_client = None
        self.note_analyzer = None
        self.question_generator = None
        self.weak_point_analyzer = None
        self.forgotten_curve = None
        self.review_scheduler = None

        if self.config.LLM_API_KEY:
            self._init_ai_components()

    def _init_ai_components(self):
        """初始化 AI 组件

        当配置了大模型 API Key 时，初始化相关 AI 组件。
        """
        self.chat_client = ChatClient(
            api_key=self.config.LLM_API_KEY,
            model=self.config.LLM_MODEL,
            base_url=self.config.LLM_BASE_URL,
        )
        print("="*50)
        print(self.chat_client.get_graph_diagram())
        print("="*50)
        self.note_analyzer = NoteAnalyzer(self.chat_client)
        self.question_generator = QuestionGenerator(self.chat_client)
        self.weak_point_analyzer = WeakPointAnalyzer(self.db)
        self.forgotten_curve = ForgottenCurve()
        logger.info("AI components initialized")

    def start_review_scheduler(self):
        """启动复习调度器

        如果配置启用了复习提醒，则启动定时调度任务。
        """
        if self.config.REVIEW_ENABLED:
            self.review_scheduler = ReviewScheduler(self.config, self.db)
            self.review_scheduler.start()
            logger.info("Review scheduler started")

    def stop(self):
        """停止应用

        关闭调度器和数据库连接。
        """
        if self.review_scheduler:
            self.review_scheduler.stop()
        self.db.close()
        logger.info("Application stopped")


def run_interactive_chat(chat_client: ChatClient):
    """运行交互式对话

    提供命令行界面，让用户与 AI 进行多轮对话。
    图内部维护完整的状态和消息历史。

    Args:
        chat_client: 聊天客户端实例
    """
    print("\n" + "="*50)
    print("欢迎使用 Algomate 算法学习助手！")
    print("输入您的问题，按回车发送。输入 'quit' 或 'exit' 退出。")
    print("="*50 + "\n")

    state = None

    while True:
        try:
            user_input = input("你: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "退出"]:
                print("\n感谢使用 Algomate，再见！")
                break

            from langchain_core.messages import HumanMessage

            if state is None:
                state = chat_client.invoke_task(
                    messages=[HumanMessage(content=user_input)]
                )
            else:
                state["messages"].append(HumanMessage(content=user_input))
                state["should_continue"] = True
                state = chat_client.invoke_task(state=state)

            response = state.get("result", "")
            if hasattr(response, 'content'):
                response = response.content
            print(f"AI: {response}\n")

            if not state.get("should_continue", True):
                print("\n对话已结束，再见！")
                break

        except KeyboardInterrupt:
            print("\n\n操作已取消，再见！")
            break
        except Exception as e:
            print(f"\n发生错误: {e}")
            logger.error(f"Chat error: {e}")


def main():
    """应用入口函数

    创建应用实例，启动调度器，并保持运行直到收到中断信号。
    """
    app = AlgomateApp()
    app.start_review_scheduler()
    logger.info("Algomate started successfully")

    if app.chat_client:
        run_interactive_chat(app.chat_client)
    else:
        print("AI 组件未初始化（可能未配置 API Key），仅运行调度器模式")
        print("按 Ctrl+C 退出...")

        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    app.stop()


if __name__ == "__main__":
    main()
