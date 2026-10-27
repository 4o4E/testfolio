FROM node:22-bookworm-slim AS web-build
WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web ./
RUN npm run build

FROM python:3.11-slim
LABEL org.opencontainers.image.title="Testfolio" \
      org.opencontainers.image.description="Read-only test results, screenshots and agent-driven recording" \
      org.opencontainers.image.source="https://github.com/4o4E/testfolio" \
      org.opencontainers.image.licenses="MIT"
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend
COPY LICENSE THIRD_PARTY_NOTICES.md LICENSES/ /usr/share/licenses/testfolio/
COPY --from=web-build /app/web/dist ./static
EXPOSE 8080 8081
CMD ["python", "-m", "backend"]
