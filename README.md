# Next book generation

## Purpose

This project is a way to play with genAI models and RAG functionalities using the [`Gutenberg project`](https://www.gutenberg.org/) data. The objective here is to provide 2 functionalities :

1. One simple functionality `AMA book` to ask questions on one selected book, using RAG.
2. One functionality to create the next volume of a selected book, using multi-agents.

## Infrastructure

This docker-compose file contains several services :

- One `ollama` service to host one model (model can be changed with the `OLLAMA_MODEL` variable within the dockerfile).
- One `qdrant` database (for the `AMA book` functionality where embeddings will be stored from the books data). Qdrant UI is available on http://localhost:6333/dashboard, to manage collections and so one.
- The main streamlit app `book_gen_app` for the UI (http://localhost:8501).

## How to run

Run `docker compose up --build`

## TODO:

- volumes redirection for qdrant db content (to avoid reloading book data for each run) and python backend code volume mount (to avoid rerunning for each code update).

<!--> podman machine init --memory=8192 --cpus=4 -->