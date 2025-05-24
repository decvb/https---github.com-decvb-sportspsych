"""
ingest_data.py

Script to ingest sports psychology documents from the ./docs directory, convert them to Markdown using MarkItDown, split them into 500-character chunks (no overlap), generate embeddings using OpenAI, and store them in Supabase PGVector via LangChain.

Usage:
    python ingest_data.py

Environment Variables Required:
    OPENAI_API_KEY
    SUPABASE_PG_CONNECTION_STRING

"""

import os
from dotenv import load_dotenv
from markitdown import MarkItDown
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores.pgvector import PGVector
from langchain.docstore.document import Document


def convert_to_markdown(file_path: str) -> str:
    """
    Converts a file to Markdown using MarkItDown.

    Args:
        file_path (str): Path to the file.

    Returns:
        str: Markdown content.
    """
    try:
        md = MarkItDown()
        result = md.convert(file_path)
        return result.text_content
    except Exception as e:
        print(f"[WARN] Could not convert {file_path} to Markdown: {e}")
        return ""

def chunk_markdown(md_text: str, chunk_size: int = 500) -> list:
    """
    Splits Markdown text into chunks of specified size.

    Args:
        md_text (str): Markdown content.
        chunk_size (int): Size of each chunk.

    Returns:
        list: List of Markdown chunks.
    """
    return [md_text[i:i+chunk_size] for i in range(0, len(md_text), chunk_size) if md_text[i:i+chunk_size].strip()]

def main():
    """
    Main ingestion workflow: converts, chunks, embeds, and stores documents.
    """
    load_dotenv()
    docs_path = './docs'
    supported_exts = ('.pdf', '.docx', '.pptx', '.xlsx', '.html', '.htm', '.txt', '.md', '.csv', '.epub')
    files = [os.path.join(docs_path, f) for f in os.listdir(docs_path) if f.lower().endswith(supported_exts)]
    if not files:
        print(f"No supported documents found in {docs_path}. Exiting.")
        return

    all_chunks = []
    for file_path in files:
        print(f"Converting {file_path} to Markdown...")
        md_text = convert_to_markdown(file_path)
        if not md_text.strip():
            continue
        chunks = chunk_markdown(md_text, chunk_size=500)
        print(f"  - {len(chunks)} chunks created from {os.path.basename(file_path)}")
        for chunk in chunks:
            # Best practice: ensure metadata is a JSON-serializable dict (not JSONB)
            # Note: PGVector will store this as JSON, not JSONB, for compatibility and easier migration.
            all_chunks.append(Document(page_content=chunk, metadata={"source": str(os.path.basename(file_path))}))

    if not all_chunks:
        print("No content to ingest after conversion and chunking. Exiting.")
        return

    # Set up OpenAI embeddings
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY not set in environment.")
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

    # Set up PGVector connection
    pg_conn_str = os.getenv("SUPABASE_PG_CONNECTION_STRING")
    if not pg_conn_str:
        raise ValueError("SUPABASE_PG_CONNECTION_STRING not set in environment.")

    # Store in PGVector
    print(f"Storing {len(all_chunks)} chunks in Supabase PGVector...")
    db = PGVector.from_documents(
        all_chunks,
        embeddings,
        connection_string=pg_conn_str,
        collection_name="sports_psych_docs"
    )
    print("Ingestion complete. Documents stored in Supabase PGVector.")


if __name__ == "__main__":
    main() 