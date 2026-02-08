# Next book generation

## Purpose

This project is a way to play with genAI models and RAG functionalities using the [`Gutenberg project`](https://www.gutenberg.org/) data. The objective here is to provide 2 functionalities :

1. One simple functionality `AMA book` to ask questions on the books, using RAG.
2. One functionality to create the next volume of a book, using multi-agents.

## Infrastructure

This docker-compose file contains several services :

- One `ollama` service to host one model (model can be changed with the `OLLAMA_MODEL` variable within the dockerfile).
- One `qdrant` database (for the `AMA book` functionality where embeddings will be stored from the books data).
- The main streamlit app `book_gen_app` for the UI.