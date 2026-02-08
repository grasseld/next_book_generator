FROM python:3.12-slim

WORKDIR /app

# Copy app files
COPY /app /app

# Install uv
RUN pip install --no-cache-dir uv==0.9.11

# Install deps
RUN --mount=type=cache,target=/tmp/book_gen_uv_cache uv sync

# # Install Streamlit
# RUN pip install --no-cache-dir streamlit

# Expose Streamlit port
EXPOSE 8501

# Run Streamlit app
CMD ["/app/.venv/bin/python", "-m", "streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]