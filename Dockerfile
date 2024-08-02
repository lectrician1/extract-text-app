FROM node:20 AS builder

ENV VITE_BASE_URL=/extract-text-app

WORKDIR /app

# Install build dependencies (for amd64 images)
RUN apt-get update && apt-get install -y \
    libcairo2-dev \
    libpango1.0-dev \
    libjpeg-dev \
    libgif-dev \
    librsvg2-dev

COPY package*.json .
RUN npm install

COPY . .

RUN NODE_ENV=production npm run build

FROM node:20 AS deployer

WORKDIR /app

COPY --from=builder /app/build build/
COPY --from=builder /app/package.json .
COPY --from=builder /app/node_modules node_modules/
COPY hasura /app/hasura

EXPOSE 3000

ENV NODE_ENV=production

CMD ["node", "build"]