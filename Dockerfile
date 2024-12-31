# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install netcat for wait-for-it.sh script
RUN apt-get update && apt-get install -y netcat-openbsd

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user for Celery
RUN adduser --disabled-password --gecos '' celeryuser

# Switch to the celeryuser for running Celery (and possibly your app as well)
USER celeryuser

# Make port 5000 available to the world outside the container
EXPOSE 5000

# Define environment variables
ENV FLASK_APP=api/v1/app.py
ENV FLASK_ENV=development

# Run the Flask app
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:5000", "api.v1.app:app"]


