@echo off
REM AlgoMate 本地开发一键启动（不依赖 Docker）
REM 双击即起后端(uv) + 前端(vite)，前端代理默认连 http://localhost:8000
setlocal
cd /d %~dp0

echo === 启动后端 (uv run uvicorn :8000) ===
start "AlgoMate-Backend" cmd /k "cd /d %~dp0 && set ALGOMATE_DB_PATH=%~dp0data\dev.db && uv run uvicorn algomate.main:app --host 0.0.0.0 --port 8000 --log-level info"

echo === 启动前端 (npm run dev :3000) ===
start "AlgoMate-Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo === 等待前端启动后打开浏览器 ===
timeout /t 8 >nul
start http://localhost:3000

echo.
echo 后端日志窗口: AlgoMate-Backend
echo 前端日志窗口: AlgoMate-Frontend
echo 关闭这两个窗口即可停止服务。
pause
endlocal
