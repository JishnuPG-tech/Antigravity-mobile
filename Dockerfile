# Use an official Python 3.10 slim image which is compatible with recent scikit-learn/pandas
FROM python:3.10-slim

# Set environment variables to prevent Python from writing pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies (if needed for TensorFlow/Scikit-learn)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set up a new user named "user" with user ID 1000
# Hugging Face Spaces requires running Docker containers as a non-root user
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Copy requirements first to leverage Docker cache
COPY --chown=user requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY --chown=user . $HOME/app

# Expose the API port 7860 for Hugging Face
EXPOSE 7860

# Command to run the application on Hugging Face port 7860
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
