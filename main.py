#!/usr/bin/env python3
"""
Algomate 统一启动脚本

同时启动前端（Vite）和后端（FastAPI）服务。

Usage:
    python main.py              # 启动全部服务（前端 + 后端）
    python main.py --backend    # 仅启动后端
    python main.py --frontend    # 仅启动前端
"""

import argparse
import subprocess
import sys
import os
import signal
import time

processes = []


def cleanup():
    """清理所有子进程"""
    print("\n正在停止所有服务...")
    for p in processes:
        try:
            p.terminate()
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()
        except Exception:
            pass
    print("所有服务已停止")


def signal_handler(signum, frame):
    """处理 Ctrl+C 信号"""
    cleanup()
    sys.exit(0)


def start_backend():
    """启动后端服务"""
    print("=" * 50)
    print("启动后端服务 (FastAPI)...")
    print("=" * 50)

    backend_dir = os.path.join(os.path.dirname(__file__), "src")

    startupinfo = None
    if sys.platform == "win32":
        CREATE_NO_WINDOW = 0x08000000
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

    proc = subprocess.Popen(
        [sys.executable, "-m", "algomate.main", "--api-only"],
        cwd=backend_dir,
        stdout=None,
        stderr=None,
        startupinfo=startupinfo,
    )
    processes.append(proc)

    print("后端服务启动中...")
    time.sleep(2)


def start_frontend():
    """启动前端服务"""
    print("=" * 50)
    print("启动前端服务 (Vite)...")
    print("=" * 50)

    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")

    if not os.path.exists(os.path.join(frontend_dir, "node_modules")):
        print("正在安装前端依赖...")
        subprocess.run(["npm", "install"], cwd=frontend_dir, check=True, shell=True)

    startupinfo = None
    creationflags = 0
    if sys.platform == "win32":
        CREATE_NO_WINDOW = 0x08000000
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        creationflags = CREATE_NO_WINDOW
        proc = subprocess.Popen(
            "npm run dev",
            cwd=frontend_dir,
            stdout=None,
            stderr=None,
            shell=True,
            startupinfo=startupinfo,
            creationflags=creationflags,
        )
    else:
        proc = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=frontend_dir,
            stdout=None,
            stderr=None,
        )
    processes.append(proc)


def main():
    global processes

    parser = argparse.ArgumentParser(description="Algomate 统一启动脚本")
    parser.add_argument(
        "--backend",
        action="store_true",
        help="仅启动后端服务"
    )
    parser.add_argument(
        "--frontend",
        action="store_true",
        help="仅启动前端服务"
    )
    args = parser.parse_args()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if args.frontend and not args.backend:
        start_frontend()
        print("\n前端服务已启动: http://localhost:3000")
        print("\n按 Ctrl+C 停止服务")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        cleanup()
        return

    if args.backend and not args.frontend:
        start_backend()
        print("\n后端服务已启动: http://localhost:8000")
        print("API 文档: http://localhost:8000/docs")
        print("\n按 Ctrl+C 停止服务")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        cleanup()
        return

    start_backend()
    time.sleep(1)
    start_frontend()

    print("\n" + "=" * 50)
    print("Algomate 全部服务已启动！")
    print("=" * 50)
    print("前端地址: http://localhost:3000")
    print("后端地址: http://localhost:8000")
    print("API 文档: http://localhost:8000/docs")
    print("\n按 Ctrl+C 停止所有服务")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    cleanup()


if __name__ == "__main__":
    main()
