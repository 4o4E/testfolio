# syntax=docker/dockerfile:1

# The generated web files are shared by all runtime architectures.
FROM --platform=$BUILDPLATFORM node:22-bookworm-slim@sha256:de170b39439eb0e5a3444ad7d60b015614a381e10fecae2e30ec9e735122f38d AS web-build
WORKDIR /app/web
COPY --link web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY --link web ./
RUN npm run build

FROM python:3.11-slim@sha256:9635410349cba3531fabde484e07f14e625abb40e1bc8b23fffa046cb497ce2d
LABEL org.opencontainers.image.title="Testfolio" \
      org.opencontainers.image.description="Read-only test results, screenshots and agent-driven recording" \
      org.opencontainers.image.source="https://github.com/4o4E/testfolio" \
      org.opencontainers.image.licenses="MIT"
WORKDIR /app
COPY --link requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --link backend ./backend
COPY --link LICENSE THIRD_PARTY_NOTICES.md LICENSES/ /usr/share/licenses/testfolio/
COPY --link --from=web-build /app/web/dist ./static
EXPOSE 8080 8081
CMD ["python", "-m", "backend"]
