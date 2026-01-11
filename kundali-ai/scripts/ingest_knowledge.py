import sys
import os
import asyncio
from typing import List

# Add the project root to the python path so we can import 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.persistence.db import AsyncSessionLocal
from app.persistence.models.knowledge_item import KnowledgeItem
from app.ai.llm_client import LLMClient

# ─────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────
DATA_FOLDER = "knowledge-base"   # Folder name
CHUNK_SIZE = 1000                # Characters per chunk
CHUNK_OVERLAP = 200              # Context overlap
# ─────────────────────────────────────────────────────────

def read_file_content(file_path: str) -> str:
    """
    Reads content from a file based on its extension (.txt or .pdf).
    Returns the text content as a string.
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
                
        elif ext == ".pdf":
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            return text
            
    except Exception as e:
        print(f"   ❌ Error reading {file_path}: {e}")
        return ""

    return ""

async def main():
    # 1. Create Folder if missing
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
        print(f"📁 Created folder '{DATA_FOLDER}'.\n👉 Please put your .txt or .pdf files inside it and run this script again.")
        return

    # 2. Find Files
    files = [f for f in os.listdir(DATA_FOLDER) if f.endswith((".txt", ".pdf"))]
    if not files:
        print(f"⚠️  No .txt or .pdf files found in '{DATA_FOLDER}'.")
        return

    # 3. Setup
    llm = LLMClient()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, 
        chunk_overlap=CHUNK_OVERLAP
    )

    print(f"🚀 Starting ingestion for {len(files)} files...")

    async with AsyncSessionLocal() as session:
        for filename in files:
            file_path = os.path.join(DATA_FOLDER, filename)
            print(f"📖 Processing: {filename}")
            
            # A. Read Content
            text = read_file_content(file_path)
            if not text.strip():
                print("   ⚠️ Skipped (Empty or unreadable)")
                continue

            # B. Split into Chunks
            chunks = splitter.split_text(text)
            print(f"   ↳ Split into {len(chunks)} chunks. Generating embeddings...")

            new_items = []
            for i, chunk in enumerate(chunks):
                # C. Generate Embedding
                # Note: Ensure your LLMClient has the get_embedding method we added earlier
                vector = await llm.get_embedding(chunk)
                
                # D. Prepare DB Object
                item = KnowledgeItem(
                    content=chunk,
                    metadata_info=f"{filename} (chunk {i+1})",
                    embedding=vector
                )
                new_items.append(item)

            # E. Save to DB
            session.add_all(new_items)
            await session.commit()
            print(f"   ✅ Saved {len(new_items)} vectors to database.")

    print("\n🎉 All done! Your RAG system is ready.")

if __name__ == "__main__":
    asyncio.run(main())