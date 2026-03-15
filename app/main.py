import streamlit as st
from load.load_books import BooksLoader
from app.next_book_gen import generate_next_book
import os
import signal
import time
import subprocess
import pathlib
import sys


def _kill_processes_on_port(port: int):
    """Kill any process listening on the given TCP port (macOS/Linux)."""
    result = subprocess.run(
        ["lsof", "-ti", f":{port}"],
        capture_output=True,
        text=True,
        check=False,
    )
    pids = [int(p) for p in result.stdout.split()] if result.stdout else []
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass

books_loader = BooksLoader()

nb_books = len(books_loader.all_books)
st.success(f"Done! {nb_books} books loaded in the vector store")

st.title("Book Generator App")
st.write("Welcome to the Book Generator!")

    # Example input form
book = st.selectbox(
    "Select one book",
    books_loader.all_books,
    format_func=lambda b: b["title"]
)

# run chainlit bot with selected book_id context
chainlit_running = True
if book:
    if st.button("Start a chat session"):
        with st.spinner("Wait for it... We are loading chat session !", show_time=True):
            env = os.environ.copy()
            env['PYTHONPATH'] = os.path.dirname(__file__)  # app directory
            env['BOOK_TITLE'] = book['title']
            env['BOOK_ID'] = str(book['id'])
            chainlit_script = str(pathlib.Path(os.path.dirname(__file__), 'app/chainlit_bot.py'))

            # If Chainlit is already running on port 9000, stop it before starting a new instance.
            _kill_processes_on_port(9000)

            chainlit_proc = subprocess.Popen([
                sys.executable,
                "-m",
                "chainlit",
                "run",
                "--port",
                "9000",
                "-h",  # headless mode
                chainlit_script,
            ], env=env)

            print("Waiting for Chainlit to start...")

            time.sleep(5)
            if chainlit_proc.poll() is not None:
                st.write("Error loading chat interface.")
                print("ERROR: Chainlit failed to start.")
                chainlit_running = False

            st.link_button(f"Go to ask question about following book: {book['title']}", "http://localhost:9000")

# generate next volume of the book
with st.container():
    st.subheader(f"Generate Next Chapters for selected book: {book['title']}")
    num_chapters = st.selectbox(
        "Select one book",
        range(0,15),
        help="Select how many chapters you want to generate for the next volume."
    )
    if st.button("Generate Next Chapter(s)"):
        expected_time = (num_chapters * 70)/60
        with st.spinner(f"Generating {num_chapters} chapter(s) for '{book['title']}' ... (expected time ~70s per chapter ~{expected_time}min)", show_time=True):
            chapters, output_file = generate_next_book(book, num_chapters)
            with open(output_file, "rb") as file:
                st.download_button(
                    label="Download & Open Book",
                    data=file,
                    file_name="generated_book.html",
                    mime="text/html"
                )