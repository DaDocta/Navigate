#!/bin/bash

# Define variables
IMAGE_NAME="my-python-app"
CONTAINER_NAME="my-python-container"

# Check if Dockerfile exists
if [[ ! -f Dockerfile ]]; then
  echo "Error: Dockerfile not found in the current directory."
  exit 1
fi

# Build the Docker image
echo "Building Docker image..."
docker build -t $IMAGE_NAME .

if [[ $? -ne 0 ]]; then
  echo "Error: Failed to build Docker image."
  exit 1
fi

# Check if a container with the same name is already running
if [[ $(docker ps -q -f name=$CONTAINER_NAME) ]]; then
  echo "Stopping existing container..."
  docker stop $CONTAINER_NAME
  echo "Removing existing container..."
  docker rm $CONTAINER_NAME
fi

# Run the Docker container
#echo "Running Docker container..."
#docker run -it --name $CONTAINER_NAME $IMAGE_NAME
