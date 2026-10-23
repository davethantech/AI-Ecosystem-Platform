FROM node:22-alpine AS build
WORKDIR /web
COPY frontend/package.json ./package.json
RUN npm install
COPY frontend/index.html ./index.html
COPY frontend/vite.config.js ./vite.config.js
COPY frontend/src ./src
RUN npm run build

FROM nginx:1.28-alpine
COPY --from=build /web/dist /usr/share/nginx/html
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
