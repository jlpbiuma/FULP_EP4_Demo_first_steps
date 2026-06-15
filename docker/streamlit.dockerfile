# Use a lightweight official Python image
FROM python:3.12-slim

# Install curl for optional container health checks and Tesseract OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tesseract-ocr \
    tesseract-ocr-spa \
    && rm -rf /var/lib/apt/lists/*

# Copy the uv binary from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy

# Establish workspace
WORKDIR /app

# Copy project files first to cache dependencies layer
COPY pyproject.toml uv.lock* ./

# Install the Python dependencies directly in system Python
RUN uv pip install --system -r pyproject.toml

# Copy the application source code
COPY . .

# Expose Streamlit default port
EXPOSE 8501

# Run the streamlit application
ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
