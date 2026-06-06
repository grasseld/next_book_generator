FROM ollama/ollama:latest

COPY ./ollama/start.sh ./start.sh
RUN chmod +x ./start.sh

ENTRYPOINT ["./start.sh"]