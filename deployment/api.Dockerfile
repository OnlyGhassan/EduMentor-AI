FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Ensure psycopg2 is installed even if it's missing from requirements.txt
RUN pip install --no-cache-dir psycopg2-binary

# Copy the entire app folder into the container
COPY app/backend /app/backend

# Expose the application port
EXPOSE 5000

# Run the FastAPI app
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "5000"]

