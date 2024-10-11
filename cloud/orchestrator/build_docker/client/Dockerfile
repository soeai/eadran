# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/go/dockerfile-reference/

#ARG PYTHON_VERSION=3.10
#FROM python:${PYTHON_VERSION}-slim as base
#FROM tensorflow/serving:latest-devel as build_image
#FROM tensorflow/tensorflow-cpu:latest      image doesnot exist
#FROM ubuntu:20.04
FROM tensorflow/tensorflow
# Prevents Python from writing pyc files.
#ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
#ENV PYTHONUNBUFFERED=1

#ENV BOOTLOADER_CC=musl-gcc

RUN mkdir -p /app
RUN mkdir -p /data
RUN mkdir -p /app/conf

WORKDIR /app

# Copy the source code into the container.
COPY . .

RUN apt update
RUN apt install -y git wget make build-essential manpages-dev python-pip

RUN pip3 install --upgrade pip setuptools wheel

RUN pip3 install --no-cache-dir -r requirements.txt

RUN chmod 755 ./start.sh

# Run the application.
ENTRYPOINT ["./start.sh"]

# ENTRYPOINT ["tail", "-f", "/dev/null"]  # DEUBUG MODE

CMD ["storage_service", "session_id", "config_file"]
