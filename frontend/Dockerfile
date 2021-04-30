FROM node:lts-alpine as build-stage

WORKDIR /app

COPY . ./

RUN yarn install

RUN yarn build

FROM nginx:stable-alpine as prod-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Override default NGINX configuration
RUN rm /etc/nginx/conf.d/default.conf
COPY conf/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
