# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install necessary packages
RUN pip install --no-cache-dir -r requirement.txt

# Expose port 8081 to the outside world
EXPOSE 8081

# Define environment variable
ENV NAME QoDService

# Run qod_evaluation.py when the container launches
CMD ["python", "qod_test.py", "http://192.168.10.234:8081", "661e92b7d3341cbe6ff0fb42", "/data/fraudTrain_processed_SMOTE_1.csv"]
