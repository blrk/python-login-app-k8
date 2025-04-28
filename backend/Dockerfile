FROM python:3.9-slim-buster

WORKDIR /app

# Copy requirements.txt first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Flask application code
COPY . .

# Set environment variables. These are *defaults* and can be overridden in Kubernetes.
ENV FLASK_SECRET_KEY="your-super-secret-key"
ENV DATABASE_HOST="postgres-service"
ENV DATABASE_PORT=5432
ENV DATABASE_NAME="mydatabase"
ENV DATABASE_USER="myuser"
# DATABASE_PASSWORD should be set via a Kubernetes Secret, not here.

EXPOSE 5000

# Run the application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app", "--workers", "3"]
