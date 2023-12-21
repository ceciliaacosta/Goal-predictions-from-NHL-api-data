# Run the Docker container with the dynamically retrieved API key
docker run -it --expose 127.0.0.1:8050:8050/tcp --env COMET_API_KEY="${COMET_API_KEY}" ift6758/serving:1.0.0
