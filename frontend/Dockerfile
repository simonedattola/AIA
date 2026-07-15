FROM node:20-slim

WORKDIR /app

COPY package.json yarn.lock* ./

RUN if [ -f yarn.lock ]; then corepack enable && yarn install --frozen-lockfile; else npm install --legacy-peer-deps --force; fi

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
