#!/usr/bin/env python3
"""
Algomate 前端启动脚本

启动前端开发服务器（Vite）。

Usage:
    python start_frontend.py
"""

import subprocess
import sys
import os

frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")

if not os.path.exists(os.path.join(frontend_dir, "node_modules")):
    print("正在安装前端依赖...")
    subprocess.run(
        ["npm", "install"],
        cwd=frontend_dir,
        check=True,
        shell=True
    )

print("=" * 50)
print("启动前端服务 (Vite)...")
print("=" * 50)

proc = subprocess.Popen(
    ["npm", "run", "dev"],
    cwd=frontend_dir,
    shell=True
)

try:
    proc.wait()
except KeyboardInterrupt:
    print("\n正在停止前端服务...")
    proc.terminate()
    proc.wait()
    print("前端服务已停止")