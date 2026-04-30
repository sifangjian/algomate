#!/usr/bin/env python3
"""
Algomate 后端启动脚本

启动后端服务（FastAPI + 修炼调度器）。

Usage:
    python start_backend.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from algomate.main import AlgomateApp

if __name__ == "__main__":
    print("=" * 50)
    print("启动后端服务...")
    print("=" * 50)

    app = AlgomateApp()
    app.start()

    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止后端服务...")
        app.stop()
        print("后端服务已停止")