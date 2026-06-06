from settings import settings
import requests
import logging

from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document

from qdrant_client.models import Distance, VectorParams
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient

book_max = 3 # number of books to process. set to float("inf") to process all books (beware of the time and resources it can take)
pmax = 3 # number of pages to fetch from the gutenberg api. set to float("inf") to fetch all available pages (beware of the time and resources it can take)

class BooksLoader():
    def __init__(self):
        """Initialize the BooksLoader by fetching the list of books and setting up the vector store (qdrant) client."""
        self.all_books = self.list_books()
        self.vector_store = self.__init_vector_store()

    def __init_vector_store(self):
        """
        Initialize the Qdrant vector store client and create the collection if it doesn't exist.
        """
        qdrant_client = QdrantClient(settings.qdrant_uri)
        embeddings = OllamaEmbeddings(model=settings.ollama_embedding_model, base_url=settings.ollama_uri)

        if not qdrant_client.collection_exists(settings.qdrant_collection):
            vector_size = len(embeddings.embed_query("sample text"))
            qdrant_client.create_collection(
                collection_name=settings.qdrant_collection,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )

        vector_store = QdrantVectorStore(
            client=qdrant_client,
            collection_name="book_collection",
            embedding=embeddings,
        )
        return vector_store

    def transform_book_content(self, content):
        """Transform the book content into smaller chunks using a text splitter.
        Args:
            content (str): The raw text content of the book.
        Returns:
            List[Document]: A list of Document objects containing the split content.
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,  # chunk size (characters)
            chunk_overlap=200,  # chunk overlap (characters)
            add_start_index=True,  # track index in original document
        )
        all_splits = text_splitter.split_documents([Document(page_content=content)])
        return all_splits

    def list_books(self):
        """
        Fetch the list of books from the Gutenberg API, handling pagination.
        Note : This loop through the pages until we reach the maximum number of pages (pmax) or there are no more pages to fetch.
        if pmax is set to float("inf"), it will fetch all available pages.
        Returns:
            List[dict]: A list of book metadata dictionaries.
        """
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
        """
        Load the content of each book into the vector store. For each book, it checks if a plain text format is available.
        If plain text is not available, it logs a warning and skips the book.
        """
        b_count = 0
        for book in self.all_books:
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
                print(f"Book {book['id']} - {book['title']} loaded with {len(splits)} chunks")
                b_count += 1
                if b_count >= book_max:
                    break
            else:
                logging.warning(f"Book {book['id']} - {book['title']} has no text/plain content available - skipped")