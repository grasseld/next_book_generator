from typing import TypedDict, List, Annotated
import operator
from langgraph.graph import StateGraph, END
from langchain_ollama import OllamaLLM
from settings import settings
import requests
import datetime
import tempfile

# history of all previous chapters - size of summary
all_chapters_summary_size = 500
# detailed chapter summary - size of summary
last_chapter_summary_size = 1000
# last part of the first book volume to give an initial "last_chapter" context to the agent
last_part_initial_book_size = 5000

generated_chapter_size = 5000

model = OllamaLLM(model=settings.ollama_model)


class BookState(TypedDict):
    # This is where your 'book' dictionary will live
    original_book: dict

    # Tracking the new volume
    new_chapters: Annotated[List[dict], operator.add] 

    # Summaries for context
    running_history: str           # Summary of all new chapters (Agent 2)
    last_chapter_details: str      # Deep dive into the very last chapter (Agent 3)

    max_chapters: int
    current_chapter_count: int

def book_to_html(book_title: str, chapters: list):
    """
    Convert a list of chapters into a single HTML book.

    Args:
        book_title (str): Title of the book
        chapters (list[str]): List of chapter text strings
    """
    output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html", prefix="book_", mode="w", encoding="utf-8")

    html = f"""<!DOCTYPE html>
        <html lang="en">
        <head>
        <meta charset="UTF-8">
        <title>{book_title}</title>
        <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.5; }}
        h1 {{ text-align: center; }}
        h2 {{ margin-top: 40px; }}
        .summary {{ font-style: italic; color: #555; margin-bottom: 20px; }}
        </style>
        </head>
        <body>
        <h1>{book_title}</h1>
        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        <hr>
    """

    for idx, chapter in enumerate(chapters, start=1):
        html += f"<h2>Chapter {idx}</h2>\n"
        html += f"<p>{chapter.replace('\n','<br>')}</p>\n"
        html += "<hr>\n"

    html += "</body></html>"

    output_file.write(html)
    output_file.close()

    print(f"Temporary HTML book saved to {output_file.name}")
    return output_file.name

def get_book_text(book_metadata: dict) -> str:
    content = requests.get(book_metadata["formats"]["text/plain; charset=utf-8"]).text
    # remove gutenberg mentions from book content
    start="*** START OF THE PROJECT GUTENBERG EBOOK"
    end="*** END OF THE PROJECT GUTENBERG EBOOK"
    return content[content.find(start) + len(start):content.find(end)]

def global_summarizer_agent(state: BookState):
    """Agent 1: Always provides the context of the original book."""
    # It pulls the summary you already have in your 'book' object
    base_summary = state["original_book"]["summary"]
    print("--- AGENT 1: Refreshed Original Context ---")
    return {"original_book_summary": f"Base Plot: {base_summary}"}

def history_computer_agent(state: BookState):
    """Agent 2: Computes summary of all NEW chapters generated so far."""
    print("--- AGENT 2: Updating Volume 2 History ---")
    if not state["new_chapters"]:
        history = state["original_book"]["content"]
        history = history[len(history)-last_part_initial_book_size:-1] # last parts of the first volume..
    else:
        # Simple logic: combine the titles or summaries of new chapters
        history = " | ".join(state["new_chapters"])

    # summarize history with LLM
    prompt = f"""
    Summarize the following text in a concise way, highlighting important events and characters.
    The summary should not be longer than {all_chapters_summary_size} chars.
    Return ONLY the summarized content directly.

    Text:
    {history}
    """
    history_summary = model.invoke(prompt)

    return {"running_history": f"Previously in this volume: {history_summary}"}

def chapter_detailer_agent(state: BookState):
    """Agent 3: Detailed focus on the immediate last chapter."""
    print("--- AGENT 3: Analyzing Last Chapter Details ---")
    if not state["new_chapters"]:
        last_chap = state["original_book"]["content"]
        last_chap = last_chap[len(last_chap)-last_part_initial_book_size:-1] # last parts of the first volume..
    else:
        last_chap = state["new_chapters"][-1]
    # summarize history with LLM TODO
    # summarize history with LLM
    prompt = f"""
    Summarize the following text in a concise way, highlighting important events and characters.
    The summary should not be longer than {last_chapter_summary_size} chars.
    Return ONLY the summarized content directly.

    Text:
    {last_chap}
    """
    last_chap_summary = model.invoke(prompt)
    details = f"Key Event: {last_chap_summary}"
    return {"last_chapter_details": details}

def writer_agent(state: BookState):
    """The Writer: Uses all 3 summaries to write the next chapter."""
    prompt = f"""
    You are a novelist writing Volume 2.
    Your task is to write a FULL STORY CHAPTER, not a summary.

    [INSTRUCTION]
    Write the full narrative of the next chapter. Do not say "In this chapter..." or "The story continues...".
    Start immediately with the action.
    Use vivid imagery, active dialogue, and internal character thoughts.

    [CONSTRAINTS]
    - STYLE: Match the tone of a professional novel.
    - LENGTH: Target approximately {generated_chapter_size} characters.
    - OUTPUT: Return ONLY the story text. No intro/outro.

    [CONTEXT ARCHIVE]
    - World Lore: '''{state['original_book']['content']}'''
    - Plot Progress: '''{state['running_history']}'''

    [THE IMMEDIATE CLIPBOARD]
    Last Chapter Ended With: '''{state['last_chapter_details']}'''

    [CHAPTER START]
    """


    # In a real app, you'd send state['original_book']['content'],
    # state['running_history'], and state['last_chapter_details'] to the LLM.

    new_chapter_data = model.invoke(prompt)

    return {
        "new_chapters": state["new_chapters"] + [new_chapter_data],
        "current_chapter_count": state["current_chapter_count"] + 1
    }

def should_continue(state: BookState):
    # This is the 'Brain' that decides if we are done
    if state["current_chapter_count"] < state["max_chapters"]:
        # Go back to the history agent to prepare for the NEXT chapter
        return "continue"
    else:
        # We reached our goal, stop the engine
        return "end"

def generate_next_book(book_metadata: dict):

    book_content = get_book_text(book_metadata)

    book_data = {
        "summary": book_metadata["summaries"][0],
        "content": book_content
    }

    # 2. Compile the graph (using the same logic from the previous response)
    # workflow.add_node(...), workflow.add_edge(...), etc.
    workflow = StateGraph(BookState)

    workflow.add_node("global_summarizer", global_summarizer_agent)
    workflow.add_node("history_computer", history_computer_agent)
    workflow.add_node("chapter_detailer", chapter_detailer_agent)
    workflow.add_node("writer", writer_agent)

    # Set the flow: 1 -> 2 -> 3
    workflow.set_entry_point("global_summarizer")
    workflow.add_edge("global_summarizer", "history_computer")
    workflow.add_edge("history_computer", "chapter_detailer")
    workflow.add_edge("chapter_detailer", "writer")

    workflow.add_conditional_edges(
        "writer",
        should_continue,
        {
            "continue": "history_computer", # Loop back to update context
            "end": END                      # Finish the book
        }
    )

    app =workflow.compile()

    initial_input = {
        "original_book": book_data,
        "new_chapters": [],
        "current_chapter_count": 0,
        "max_chapters": 2  # This will trigger 2 loops
    }

    print("Starting the Book Generation Engine...\n")
    for output in app.stream(initial_input):
        # This loop in Python just lets us see the internal LangGraph steps
        for node, data in output.items():
            if node == "writer":
                print("✅ Finished chapter")
    return data


# for testing outside st app..

book_metadata = {
    "id": 84,
    "summaries": [
        "\"Frankenstein; Or, The Modern Prometheus\" by Mary Wollstonecraft Shelley is a Gothic novel published in 1818. It tells the story of Victor Frankenstein, a young scientist who creates a living creature from assembled body parts in an unorthodox experiment. When the creature awakens, Victor flees in horror, abandoning his creation. The conscious being must navigate a world that fears him, learning language and seeking connection, only to face repeated rejection. Embittered and alone, the creature confronts his creator with a desperate request that will set both on a dark path of vengeance and tragedy. (This is an automatically generated summary.)"
    ]
}

book_metadata["formats"] = {}
book_metadata["formats"]["text/plain; charset=utf-8"] = "https://www.gutenberg.org/ebooks/84.txt.utf-8"

generated_chapters = generate_next_book(book_metadata)
print("end")

# TODO: save data chapters into a PDF