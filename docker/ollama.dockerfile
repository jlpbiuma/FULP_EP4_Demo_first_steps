FROM ollama/ollama:latest

# Start Ollama server in the background, wait for it to be ready, pull the llama3.1 model, and exit
RUN ollama serve & \
    until ollama list >/dev/null 2>&1; do sleep 1; done && \
    ollama pull llama3.1
