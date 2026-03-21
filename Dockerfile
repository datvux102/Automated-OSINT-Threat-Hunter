FROM node:20-bookworm AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.10-slim AS runtime
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY src/ ./src/
COPY prompts/ ./prompts/
COPY pyproject.toml README.md ./
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

EXPOSE 8000
ENV PORT=8000

CMD ["python", "-m", "cybersentinel.web_server"]
