FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# Create upload directory
RUN mkdir -p /app/uploads

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Non-root user
RUN useradd -m -u 1000 hoard && \
    chown -R hoard:hoard /app
USER hoard

EXPOSE 8000

ENTRYPOINT ["bash", "entrypoint.sh"]
