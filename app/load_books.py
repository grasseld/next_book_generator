from settings import settings
import requests
import logging

from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document

from qdrant_client.models import Distance, VectorParams
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient

pmax = 10 # Max number of pages to query from gutenberg (for dev purposed, set to -1 to query all pages)

class BooksLoader():
    def __init__(self):
        self.list_books = self.list_books()
        self.vector_store = self.__init_vector_store()

    def __init_vector_store(self):
        qdrant_client = QdrantClient("http://localhost:6333")
        embeddings = OllamaEmbeddings(model="tinyllama", base_url="http://localhost:11434")

        if not qdrant_client.collection_exists(settings.qdrant_collection):
            vector_size = len(embeddings.embed_query("sample text"))
            qdrant_client.create_collection(
                collection_name=settings.qdrant_collection,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )

        vector_store = QdrantVectorStore(
            client=qdrant_client,
            collection_name=settings.qdrant_collection,
            embedding=embeddings,
        )
        return vector_store

    def transform_book_content(self, content):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # chunk size (characters)
            chunk_overlap=200,  # chunk overlap (characters)
            add_start_index=True,  # track index in original document
        )
        all_splits = text_splitter.split_documents([Document(page_content=content)])
        return all_splits

    def list_books(self):
        query_result = requests.get(settings.gutenberg_uri).json()
        list_books = []
        end_page = False
        p_count = 0
        while not end_page and p_count < pmax:
            list_books = list_books + query_result["results"]
            if query_result["next"] is not None:
                query_result = requests.get(query_result["next"]).json()
            else:
                end_page = True
            p_count += 1
        return list_books

    def load_books_content(self):
        for book in self.list_books:
            if "text/plain; charset=utf-8" in book["formats"]:
                content = requests.get(book["formats"]["text/plain; charset=utf-8"]).text
                splits = self.transform_book_content(content)
                docs_with_meta = [
                    Document(
                        page_content=split.page_content if hasattr(split, 'page_content') else split,
                        metadata={**book}
                    )
                    for split in splits
                ]
                _ = self.vector_store.add_documents(documents=docs_with_meta)
            else:
                logging.warning(f"Book {book['id']} - {book['title']} has no text/plain content available - skipped")