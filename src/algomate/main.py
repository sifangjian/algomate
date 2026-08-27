"""
Algomate 主程序模块

算法修习助手主程序入口，负责：
- 应用初始化和配置
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
from .core.memory.forgetting_curve import ForgettingCurveEngine
from .core.scheduler.review_scheduler import ReviewScheduler

logger = logging.getLogger(__name__)

_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"


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
        logging.Formatter(_LOG_FORMAT)
    )
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter(_LOG_FORMAT)
    )
    logger.addHandler(file_handler)


class AlgomateApp:
    """算法修习助手应用类

    应用主类，负责整体组件的初始化和管理。

    Attributes:
        config: 应用配置
        db: 数据库实例
        forgetting_curve: 遗忘曲线算法
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
        self.forgetting_curve = ForgettingCurveEngine()
        self.review_scheduler = None
        self.api_server = None
        self.api_server_thread = None

        self._init_api_server()

    def start_review_scheduler(self):
        """启动修炼调度器"""
        self.review_scheduler = ReviewScheduler(db=self.db, config=self.config)
        self.review_scheduler.start()
        logger.info("Review scheduler started")

    def _init_api_server(self):
        """初始化 FastAPI 服务器

        创建 FastAPI 应用实例，并注册所有路由。
        """
        from fastapi import FastAPI, HTTPException
        from fastapi.middleware.cors import CORSMiddleware

        self.api_app = FastAPI(
            title="算法修习助手 API",
            version="1.0.0",
        )

        @self.api_app.exception_handler(Exception)
        async def global_exception_handler(request, exc):
            logger.error(
                "Unhandled exception on %s %s: %s",
                request.method, request.url.path, exc,
                exc_info=True,
            )
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=500,
                content={"detail": str(exc)},
            )

        @self.api_app.exception_handler(HTTPException)
        async def http_exception_handler(request, exc):
            if exc.status_code >= 500:
                logger.error(
                    "HTTP %d on %s %s: %s",
                    exc.status_code, request.method, request.url.path, exc.detail,
                )
            elif exc.status_code >= 400:
                logger.warning(
                    "HTTP %d on %s %s: %s",
                    exc.status_code, request.method, request.url.path, exc.detail,
                )
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
            )

        self.api_app.add_middleware(
            CORSMiddleware,
            # Dev 阶段临时放开 CORS，便于 Chrome 扩展直接调用
            # TODO: 正式部署时收紧为前端域名列表
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        from .api.v1.router import router as v1_router
        self.api_app.include_router(v1_router, prefix="/api/v1")

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


def main():
    """应用入口函数

    创建应用实例，启动全部服务（API 服务器 + 修炼调度器）。
    """
    import argparse

    parser = argparse.ArgumentParser(description="Algomate 算法修习助手")
    parser.add_argument(
        "--api-only",
        action="store_true",
        help="仅启动后端 API 服务（不启动修炼调度器）"
    )
    args = parser.parse_args()

    app = AlgomateApp()

    if args.api_only:
        print("启动 API 服务模式...")
        app.start_api_only()
    else:
        app.start()
        logger.info("Algomate started successfully")

        print("系统运行中，按 Ctrl+C 退出...")
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            pass

        app.stop()


app = AlgomateApp().api_app


if __name__ == "__main__":
    main()