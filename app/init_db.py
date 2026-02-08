from log import configure_logging
from load_books import BooksLoader

configure_logging()

if __name__ == "__main__":
    bl = BooksLoader()
    bl.load_books_content()