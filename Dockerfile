# Use official Python base image
FROM python:3.11-slim

# Set environment
ENV PYTHONUNBUFFERED=1

# Set working directory inside container
WORKDIR /code

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app code into the container
COPY . .

# Expose port (FastAPI default is 8000)
EXPOSE 8000

# Start FastAPI with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
