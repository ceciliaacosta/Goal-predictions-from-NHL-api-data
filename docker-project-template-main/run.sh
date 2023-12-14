# Retrieve the Comet API key from the local machine environment variable
COMET_API_KEY=${COMET_API_KEY}

# Run the Docker container with the dynamically retrieved API key
docker run -p 8050:8050 -e COMET_API_KEY="${COMET_API_KEY}" hockey-app
