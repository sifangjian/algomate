#!/usr/bin/env bash
# Algomate 服务器端部署 / 更新脚本
# 用法(在仓库根目录):
#   bash deploy.sh          # 首次部署或拉取最新代码后重启
#   bash deploy.sh pull     # 先 git pull 再重启
#
# 前提:
#   - 服务器已装 Docker + Docker Compose v2+
#   - 本仓库已 git clone 到服务器某目录
#   - 外层反向代理(nginx/caddy)已配置:
#       www.fjsi.top/     -> localhost:3000
#       www.fjsi.top/api  -> localhost:8000
#   - 数据持久化在 ./data（首次启动自动建空库，或把旧 data/ 拷过来）

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [ "$1" = "pull" ]; then
  echo "==> git pull 最新代码"
  git pull --ff-only || { echo "git pull 失败，请手动处理冲突"; exit 1; }
fi

echo "==> 停止旧容器"
docker compose down || true

echo "==> 构建并启动 (后台)"
# --build 仅首次或依赖变更需要；纯代码改动用 restart 即可
# 这里统一 build 以保证依赖同步（pyproject / package.json 变更时必需）
docker compose up -d --build

echo "==> 等待后端健康"
for i in $(seq 1 30); do
  if docker inspect -f '{{.State.Health.Status}}' algomate-backend 2>/dev/null | grep -q healthy; then
    echo "后端健康 OK"
    break
  fi
  sleep 2
done

echo "==> 部署完成"
echo "前端: http://localhost:3000  (经反代 www.fjsi.top/)"
echo "后端: http://localhost:8000  (经反代 www.fjsi.top/api)"
docker compose ps
