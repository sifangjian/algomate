# 前端 Dockerfile
# 使用 Node 20 以兼容 vitest 4 / rolldown（需要 node >= 20.12）

FROM node:20-alpine

WORKDIR /app

# 复制依赖文件
COPY package*.json ./

# 配置 npm 使用淘宝镜像源
RUN npm config set registry https://registry.npmmirror.com

# 安装依赖
# 使用 npm i 而非 npm ci：npm ci 存在已知 bug，会遗漏 rolldown 的平台原生绑定
# （如 @rolldown/binding-linux-x64-musl），导致 vitest 4 无法加载
RUN npm i

EXPOSE 3000

# 启动开发服务器
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]