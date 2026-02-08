import streamlit as st

st.title("Book Generator App")
st.write("Welcome to the Book Generator!")

# Example input form
book_title = st.text_input("Book Title")
book_universe = st.text_area("Describe the universe/elements")

if st.button("Generate Next Chapter"):
	st.info(f"Generating next chapter for '{book_title}' in universe: {book_universe}")