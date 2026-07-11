# 前端 Dockerfile

FROM node:18-alpine

WORKDIR /app

# 复制依赖文件
COPY package*.json ./

# 配置 npm 使用淘宝镜像源
RUN npm config set registry https://registry.npmmirror.com

# 安装依赖
RUN npm ci

EXPOSE 3000

# 启动开发服务器
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]