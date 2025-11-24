# Use a slim Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system deps (optional, but nice to have curl etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . /app

# Expose the port FastAPI will run on
EXPOSE 7860

# Command to run the app (Hugging Face expects the app on port 7860)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
