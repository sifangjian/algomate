#!/usr/bin/env bash
# AlgoMate 本地一键前后端启动脚本
# 用法: bash scripts/dev.sh   (在仓库根目录运行)
# 后端: FastAPI @ :8000  (显式指定项目内数据库, 避免落到 /app/data)
# 前端: Vite   @ :3000
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DB_PATH="$ROOT/data/algomate.db"
cd "$ROOT"

echo "==> 项目根: $ROOT"
echo "==> 数据库: $DB_PATH"

# 停掉可能残留的 8000/3000 占用进程(单斜杠 taskkill)
for port in 8000 3000; do
  pid=$(netstat -ano 2>/dev/null | grep ":$port " | awk '{print $5}' | head -1)
  if [ -n "$pid" ]; then
    echo "==> 清理端口 $port 残留进程 PID=$pid"
    taskkill //F //PID "$pid" >/dev/null 2>&1 || true
  fi
done
sleep 1

# 后端 (background)
echo "==> 启动后端 :8000"
ALGOMATE_DB_PATH="$DB_PATH" uv run --no-sync uvicorn algomate.main:app --host 0.0.0.0 --port 8000 --reload > "$ROOT/data/backend.log" 2>&1 &
BACK_PID=$!
echo "    后端 PID=$BACK_PID (日志: data/backend.log)"

# 前端 (background)
echo "==> 启动前端 :3000"
cd "$ROOT/frontend"
npm run dev > "$ROOT/data/frontend.log" 2>&1 &
FRONT_PID=$!
echo "    前端 PID=$FRONT_PID (日志: data/frontend.log)"

echo ""
echo "就绪: 前端 http://localhost:3000 | 后端 http://localhost:8000"
echo "Ctrl+C 不会结束后台进程; 如需停止运行: taskkill //F //PID $BACK_PID 与 $FRONT_PID"
