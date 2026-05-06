"""
Algomate 主程序模块

算法修习助手主程序入口，负责：
- 应用初始化和配置
- AI 组件的初始化
- 修炼调度器的启动和管理
- 日志系统配置
- FastAPI 服务器管理（后端 API）
- 前后端统一启动

Usage:
    from src.algomate.main import AlgomateApp

    app = AlgomateApp()
    app.start()  # 启动全部服务（后端 API + 修炼调度器）
    # 或
    app.start_api_only()  # 仅启动后端 API
"""

import logging
import sys
import threading
from pathlib import Path

from algomate.config.settings import AppConfig
from .data.database import Database
from .core.agent.chat_client import ChatClient
from .core.agent.content_analyzer import ContentAnalyzer
from .core.agent.question_generator import QuestionGenerator
from .core.agent.weak_point_analyzer import WeakPointAnalyzer
from .core.memory.forgotten_curve import ForgottenCurveEngine
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

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logging.getLogger().addHandler(console_handler)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logging.getLogger().addHandler(file_handler)


class AlgomateApp:
    """算法修习助手应用类

    应用主类，负责整体组件的初始化和管理。

    Attributes:
        config: 应用配置
        db: 数据库实例
        chat_client: AI 对话客户端
        content_analyzer: 内容分析器
        question_generator: 试炼生成器
        weak_point_analyzer: 薄弱点分析器
        forgotten_curve: 遗忘曲线算法
        review_scheduler: 修炼调度器
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
        self.content_analyzer = None
        self.question_generator = None
        self.weak_point_analyzer = None
        self.forgotten_curve = None
        self.review_scheduler = None
        self.api_server = None
        self.api_server_thread = None

        if self.config.LLM_API_KEY:
            self._init_ai_components()

        self._init_api_server()

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
        self.content_analyzer = ContentAnalyzer(self.chat_client)
        self.question_generator = QuestionGenerator(self.chat_client)
        self.weak_point_analyzer = WeakPointAnalyzer(self.db)
        self.forgotten_curve = ForgottenCurveEngine()
        logger.info("AI components initialized")

    def start_review_scheduler(self):
        """启动修炼调度器

        如果配置启用了修炼提醒，则启动定时调度任务。
        """
        if self.config.REVIEW_ENABLED:
            self.review_scheduler = ReviewScheduler(db=self.db, config=self.config)
            self.review_scheduler.start()
            logger.info("Review scheduler started")

    def _init_api_server(self):
        """初始化 FastAPI 服务器

        创建 FastAPI 应用实例，并注册所有路由。
        """
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware

        self.api_app = FastAPI(
            title="算法修习助手 API",
            version="1.0.0",
        )

        self.api_app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        from .api import routes
        self.api_app.include_router(routes.router, prefix="/api")

        from .api.hall_routes import router as hall_router
        self.api_app.include_router(hall_router)

        from .models import (
            notes_router,
            cards_router,
            bosses_router,
            npcs_router,
            questions_router,
            answers_router,
            dialogues_router,
            review_records_router,
            learning_progress_router,
        )
        self.api_app.include_router(notes_router)
        self.api_app.include_router(cards_router)
        self.api_app.include_router(bosses_router)
        self.api_app.include_router(npcs_router)
        self.api_app.include_router(questions_router)
        self.api_app.include_router(answers_router)
        self.api_app.include_router(dialogues_router)
        self.api_app.include_router(review_records_router)
        self.api_app.include_router(learning_progress_router)
        logger.info("FastAPI server initialized")

    def start_api_server(self):
        """启动 FastAPI 服务器（在独立线程中）"""
        if self.api_server is None:
            import uvicorn
            self.api_server = uvicorn.Server(
                uvicorn.Config(
                    self.api_app,
                    host="0.0.0.0",
                    port=8000,
                    log_level="info",
                )
            )
            self.api_server_thread = threading.Thread(
                target=self.api_server.run,
            )
            self.api_server_thread.start()
            logger.info("FastAPI server started on http://0.0.0.0:8000")

    def start_api_only(self):
        """仅启动后端 API 服务（不启动修炼调度器）"""
        self.start_api_server()
        logger.info("API server running. Press Ctrl+C to stop.")
        try:
            while self.api_server_thread.is_alive():
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("API server stopped by user")
            self.stop()
            self.api_server_thread.join(timeout=5)
            logger.info("API server thread joined")

    def start(self):
        """启动全部服务

        启动后端 API 服务器和修炼调度器。
        """
        self.start_api_server()
        self.start_review_scheduler()
        logger.info("All services started successfully")

    def stop(self):
        """停止应用

        关闭 API 服务器、调度器和数据库连接。
        """
        if self.api_server:
            self.api_server.should_exit = True
        if self.review_scheduler:
            self.review_scheduler.stop()
        self.db.close()
        self.api_server = None
        self.api_server_thread = None
        logger.info("Application stopped")


def run_interactive_chat(chat_client: ChatClient):
    """运行交互式对话

    提供命令行界面，让用户与 AI 进行多轮对话。
    图内部维护完整的状态和消息历史。

    Args:
        chat_client: 聊天客户端实例
    """
    print("\n" + "="*50)
    print("欢迎使用 Algomate 算法修习助手！")
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

    创建应用实例，启动全部服务（API 服务器 + 修炼调度器 + 交互式对话）。
    """
    import argparse

    parser = argparse.ArgumentParser(description="Algomate 算法修习助手")
    parser.add_argument(
        "--api-only",
        action="store_true",
        help="仅启动后端 API 服务（不启动交互式对话）"
    )
    args = parser.parse_args()

    app = AlgomateApp()

    if args.api_only:
        print("启动 API 服务模式...")
        app.start_api_only()
    else:
        app.start()
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
