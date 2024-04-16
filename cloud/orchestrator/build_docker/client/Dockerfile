# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/go/dockerfile-reference/

#ARG PYTHON_VERSION=3.10
#FROM python:${PYTHON_VERSION}-slim as base
#FROM tensorflow/serving:latest-devel as build_image
FROM tensorflow/tensorflow-cpu:latest
#FROM ubuntu:20.04
# Prevents Python from writing pyc files.
#ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
#ENV PYTHONUNBUFFERED=1

#ENV BOOTLOADER_CC=musl-gcc

RUN mkdir -p /app

WORKDIR /app

# Copy the source code into the container.
COPY . .

RUN apt update
RUN apt install -y git wget make build-essential manpages-dev python3-pip

RUN pip3 install --upgrade pip setuptools wheel

RUN pip3 install --no-cache-dir -r requirements.txt

RUN chmod 755 ./start.sh

# Run the application.
ENTRYPOINT ["./start.sh"]
CMD ["http://192.168.10.234:8081", "661e92b7d3341cbe6ff0fb42"]
