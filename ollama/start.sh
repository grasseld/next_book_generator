#!/bin/sh

ollama serve &

# wait for server to be ready
until ollama list > /dev/null 2>&1; do
  sleep 2
done

ollama pull llama3
ollama pull nomic-embed-text

wait