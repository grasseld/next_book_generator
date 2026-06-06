from load.load_books import BooksLoader
import time


start_time = time.time()
books_loader = BooksLoader()
books_loader.load_books_content()
end_time = time.time()
print(f"Execution time: {end_time - start_time} seconds")
print("end")