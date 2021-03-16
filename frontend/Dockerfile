FROM node:lts-alpine as build-stage

WORKDIR /app

COPY package*.json ./
COPY yarn* ./

RUN yarn install

COPY . .
RUN yarn build

FROM nginx:stable-alpine as prod-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
