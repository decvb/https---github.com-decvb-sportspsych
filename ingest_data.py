"""
ingest_data.py

Script to ingest all documents in the /docs directory, convert to Markdown (if needed), chunk with overlap, embed using OpenAI, and store in Supabase PGVector via LangChain.

Usage: python ingest_data.py

Environment variables required (see .env):
- OPENAI_API_KEY
- SUPABASE_URL
- SUPABASE_SERVICE_KEY (or DB connection string)

Follows project conventions and best practices.
"""

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader, UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores.pgvector import PGVector

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_PG_CONN_STRING = os.getenv("SUPABASE_PG_CONNECTION_STRING")

DOCS_DIR = Path("docs")
CHUNK_SIZE = 800
CHUNK_OVERLAP = 200


def get_all_doc_paths(docs_dir: Path) -> List[Path]:
    """
    Recursively get all text/markdown files in the docs directory.

    Args:
        docs_dir (Path): Path to the docs directory.

    Returns:
        List[Path]: List of file paths.
    """
    return [p for p in docs_dir.rglob("*") if p.is_file() and p.suffix in {".md", ".txt"}]


def load_and_convert_to_markdown(file_path: Path) -> str:
    """
    Load a file and convert to Markdown if needed.

    Args:
        file_path (Path): Path to the file.

    Returns:
        str: Markdown content.
    """
    if file_path.suffix == ".md":
        loader = UnstructuredMarkdownLoader(str(file_path))
    else:
        loader = TextLoader(str(file_path))
    docs = loader.load()
    return docs[0].page_content if docs else ""


def chunk_document(text: str) -> List[str]:
    """
    Chunk a document using RecursiveCharacterTextSplitter with overlap.

    Args:
        text (str): The document text.

    Returns:
        List[str]: List of text chunks.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", "!", "?", " "]
    )
    return splitter.split_text(text)


def main():
    """
    Main ingestion workflow: load, convert, chunk, embed, and store documents.
    """
    if not OPENAI_API_KEY or not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise EnvironmentError("Missing required environment variables. Check .env file.")

    doc_paths = get_all_doc_paths(DOCS_DIR)
    all_chunks = []
    metadatas = []

    for path in doc_paths:
        print(f"Processing {path}...")
        markdown = load_and_convert_to_markdown(path)
        if not markdown.strip():
            print(f"Warning: {path} is empty or could not be loaded.")
            continue
        chunks = chunk_document(markdown)
        all_chunks.extend(chunks)
        metadatas.extend([{"source": str(path), "chunk": i} for i in range(len(chunks))])

    print(f"Total chunks to embed: {len(all_chunks)}")

    # Set up embeddings and vector store
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    # Prefer full connection string from env if provided
    if SUPABASE_PG_CONN_STRING:
        connection_string = SUPABASE_PG_CONN_STRING
    else:
        connection_string = f"postgresql+psycopg2://postgres:{SUPABASE_SERVICE_KEY}@{SUPABASE_URL.replace('https://', '').replace('.supabase.co', '.supabase.co:5432')}/postgres"
    vectorstore = PGVector(
        connection_string=connection_string,
        collection_name="sports_psychology_docs",
        embedding_function=embeddings,
    )

    # Add to vector store
    vectorstore.add_texts(all_chunks, metadatas=metadatas)
    print("Ingestion complete.")


if __name__ == "__main__":
    main() 