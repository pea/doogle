FROM node:18.14.1-alpine

EXPOSE 4000

ADD ./api/ /app/
WORKDIR /app
RUN npm i

CMD ["npm", "start"]
