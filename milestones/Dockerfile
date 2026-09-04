# Stage 1: Build the React frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Setup FastAPI backend
FROM python:3.13-slim
WORKDIR /app

# Install system dependencies needed for python packages (if any)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend assets
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Expose the port
EXPOSE 8000

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8000
# DATABASE_URL should be provided by the host environment (Render, Neon, etc.)

# Run uvicorn
CMD uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
