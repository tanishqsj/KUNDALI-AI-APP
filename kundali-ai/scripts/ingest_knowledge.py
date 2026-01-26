import sys
import os
import asyncio
import argparse
from typing import List

# Add the project root to the python path so we can import 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.persistence.db import AsyncSessionLocal
from app.persistence.models.knowledge_item import KnowledgeItem
from app.ai.llm_client import LLMClient

# ─────────────────────────────────────────────────────────
# CONFIGURATION (Defaults)
# ─────────────────────────────────────────────────────────
DATA_FOLDER = "knowledge-base/cleaned"   # Target the cleaned data folder
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

async def main(mode: str = "add"):
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

    print(f"🚀 Starting ingestion (Mode: {mode.upper()}) for {len(files)} files...")

    async with AsyncSessionLocal() as session:
        # 0. Clear existing data if overwrite mode
        if mode == "overwrite":
            print("🗑️  Clearing existing knowledge items...")
            from sqlalchemy import delete
            await session.execute(delete(KnowledgeItem))
            await session.commit()
            print("   ✅ Old data cleared.")
        else:
            print("   ⏩ Incremental mode: Preserving existing data.")

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
                # C. Classify Content (Category & Keywords)
                classification_prompt = (
                    "Analyze the following Vedic Astrology text and classify it into ONE of these categories: "
                    "dharma (spirituality/duty), artha (career/wealth), kama (relationships/desire), "
                    "moksha (liberation/loss), health, or general.\n"
                    "Also extract 3-5 keywords.\n"
                    "Format: Category | Keywords\n"
                    f"Text: {chunk[:500]}..."
                )
                
                try:
                    # Simple classification call
                    cls_response = await llm.complete(
                        system_prompt="You are a Vedic Astrology classifier. Output ONLY the format: Category | Keywords",
                        user_prompt=classification_prompt
                    )
                    
                    if "|" in cls_response:
                        cat_raw, kw_raw = cls_response.split("|", 1)
                        category = cat_raw.strip().lower()
                        keywords = kw_raw.strip()
                    else:
                        category = "general"
                        keywords = ""
                        
                    print(f"      • [{category}] {keywords[:30]}...")
                    
                except Exception as e:
                    print(f"      ⚠️ Classification failed: {e}")
                    category = "general"
                    keywords = ""

                # D. Generate Embedding
                vector = await llm.get_embedding(chunk)
                
                # E. Prepare DB Object
                item = KnowledgeItem(
                    content=chunk,
                    metadata_info=f"{filename} (chunk {i+1})",
                    category=category,
                    keywords=keywords,
                    embedding=vector
                )
                new_items.append(item)

            # E. Save to DB
            session.add_all(new_items)
            await session.commit()
            print(f"   ✅ Saved {len(new_items)} vectors to database.")

    print("\n🎉 All done! Your RAG system is ready.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest knowledge base documents into RAG.")
    parser.add_argument(
        "--mode", 
        choices=["add", "overwrite"], 
        default="add",
        help="Ingection mode: 'add' (incremental) or 'overwrite' (clear DB first)."
    )
    args = parser.parse_args()
    
    asyncio.run(main(mode=args.mode))