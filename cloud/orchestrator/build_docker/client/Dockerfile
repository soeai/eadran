# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/go/dockerfile-reference/

ARG PYTHON_VERSION=3.10
FROM python:${PYTHON_VERSION}-slim as base

# Prevents Python from writing pyc files.
#ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
#ENV PYTHONUNBUFFERED=1

ENV BOOTLOADER_CC=musl-gcc

RUN mkdir -p /app

WORKDIR /app

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/go/dockerfile-user-best-practices/
#ARG UID=10001
#RUN #adduser \
#    --disabled-password \
#    --gecos "" \
#    --home "/nonexistent" \
#    --shell "/sbin/nologin" \
#    --no-create-home \
#    --uid "${UID}" \
#    appuser

# Copy the source code into the container.
COPY . .
RUN apt update
RUN apt install -y git wget make build-essential manpages-dev python3-pip

RUN pip3 install --upgrade pip

RUN pip3 install --no-cache-dir -r requirements.txt

#RUN #apt update && apt install -y gcc musl-dev python3-dev wget

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into
# into this layer.
#RUN --mount=type=cache,target=/root/.cache/pip \
#    --mount=type=bind,source=requirements.txt,target=requirements.txt \
#    python -m pip install -r requirements.txt

# Switch to the non-privileged user to run the application.
#USER appuser

# Expose the port that the application listens on.
#EXPOSE 8080

RUN chmod 755 ./start.sh

# Run the application.
#CMD ["./start.sh"]
ENTRYPOINT ["./start.sh"]
CMD ["http://192.168.10.234:8081/storage/obj", "661e3dded3341cbe6ff0fb3d"]
