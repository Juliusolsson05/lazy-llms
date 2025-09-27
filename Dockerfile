# LLM-Native Project Management - Jira-lite
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY Makefile .
COPY docs/ ./docs/

# Create data directory for SQLite database
RUN mkdir -p /app/data

# Create non-root user for security
RUN groupadd -r jira_lite && useradd -r -g jira_lite jira_lite
RUN chown -R jira_lite:jira_lite /app
USER jira_lite

# Expose port
EXPOSE 1929

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:1929/api/health || exit 1

# Default command
CMD ["python", "-m", "src.jira_lite.app", "--port", "1929", "--host", "0.0.0.0", "--auto"]