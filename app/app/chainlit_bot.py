import chainlit as cl
from retrieval.retriever import Retriever
from langchain_ollama import OllamaLLM
from settings import settings
import os


retrieval = Retriever()
model = OllamaLLM(model=settings.ollama_model, base_url=settings.ollama_uri)


show_retrieved_chunks = True

# for dev purposes..

#os.environ["BOOK_ID"] = "84"
#os.environ["BOOK_TITLE"] = "Frankenstein; Or, The Modern Prometheus by Mary Wollstonecraft Shelley"

# localhost:9000/?book_id=84&book_title=Frankenstein;%20Or,%20The%20Modern%20Prometheus%20by%20Mary%20Wollstonecraft%20Shelley
# calling chainlit with query params : https://github.com/Chainlit/chainlit/issues/144

@cl.on_chat_start
async def on_chat_start():
    # get book context from env variables
    book_id = os.environ.get("BOOK_ID", None)
    book_title = os.environ.get("BOOK_TITLE", None)


    cl.user_session.set("book_id", book_id)
    cl.user_session.set("book_title", book_title)
    if book_title is None:
        msg = "New chat session started - book_id/book_title are missing from context. you can ask me anything but I won't be able to provide specific answers about the book without it."
    else:
        msg = f"New chat session started - Book Assistant is here to help you ! You can ask question about book `{book_title}`"
    await cl.Message(content=msg).send()

@cl.on_message
async def on_message(msg: cl.Message):
    book_id = cl.user_session.get("book_id")
    if book_id is not None:
        similar_chunks = retrieval.retrieve_similar_chunks(prompt=msg.content, book_id=int(book_id), top_k=settings.top_k_retrieval)
        similar_chunks = [chunk.page_content for chunk in similar_chunks]
        similar_chunks_str = "\n\n".join(similar_chunks)
        prompt = f"""
            You are a helpful assistant answering questions about books.

            Use ONLY the provided context to answer the question.
            If the answer is not in the context, say you don't know.

            Context:
            {similar_chunks_str}

            Question:
            {msg.content}

            Answer:
        """
        answer = await model.ainvoke(prompt)
        if show_retrieved_chunks:
            answer = f"Answer:\n{answer}\n\nRetrieved Chunks:\n{similar_chunks_str}"
        await cl.Message(content=answer).send()
    else:
        answer = await model.ainvoke(msg.content)
        await cl.Message(content=answer).send()