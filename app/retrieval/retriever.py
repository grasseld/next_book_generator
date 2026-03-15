
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document

from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from settings import settings


class Retriever():
    def __init__(self):
        """Initialize the Retriever with a vector store client.
        Args:
            vector_store: An instance of a vector store client (e.g., Qdrant).
        """
        # embeddings model
        self.embeddings = OllamaEmbeddings(model=settings.ollama_model, base_url=settings.ollama_uri)
        # vector store client
        qdrant_client = QdrantClient(settings.qdrant_uri)
        self.vector_store = QdrantVectorStore(
            client=qdrant_client,
            collection_name=settings.qdrant_collection,
            embedding=self.embeddings,
        )


    def retrieve_similar_chunks(self, prompt, book_id, top_k=5):
        """Retrieve similar chunks from the vector store based on the query.
        Args:
            prompt (str): The input prompt for which to find similar chunks.
            book_id (str): The ID of the book for which to find similar chunks.
            top_k (int): The number of top similar chunks to retrieve.
        Returns:
            List[Document]: A list of Document objects containing the similar chunks.
        """
        similar_chunks = self.vector_store.similarity_search(
            prompt,
            k=top_k,
            filter={
                "must": [
                    {
                        "key": "metadata.id",
                        "match": {"value": book_id}
                    }
                ]
            },
        )
        return similar_chunks