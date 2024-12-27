# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside the container
EXPOSE 5000

# Define environment variable
# ENV FLASK_APP=app.py
ENV FLASK_APP=api/v1/app.py
ENV FLASK_ENV=development

# Run the Flask app
# CMD ["flask", "run", "--host=0.0.0.0"]
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "api.v1.app:app"]
