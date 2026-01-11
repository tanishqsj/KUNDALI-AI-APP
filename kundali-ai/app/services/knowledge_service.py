from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.persistence.repositories.knowledge_repo import KnowledgeRepository
from app.ai.llm_client import LLMClient

class KnowledgeService:
    def __init__(self):
        self.llm_client = LLMClient()

    async def retrieve_context(
        self, 
        session: AsyncSession, 
        query: str, 
        limit: int = 3
    ) -> List[str]:
        # 1. Log the attempt
        print(f"\n🔎 [RAG] Searching knowledge for: '{query}'")

        # 2. Get Embedding
        query_vector = await self.llm_client.get_embedding(query)

        # 3. Search DB
        repo = KnowledgeRepository(session)
        items = await repo.search_similar(query_vector, limit=limit)
        
        # 4. Process and Log Results
        context_data = []
        
        if items:
            print(f"✅ [RAG] Found {len(items)} relevant chunks:")
            for i, item in enumerate(items):
                # Clean up the filename to look like a Book Title
                # e.g., "phaldeepika.txt" -> "Phaldeepika"
                raw_source = item.metadata_info or "Unknown Source"
                source_name = raw_source.replace(".txt", "").replace(".pdf", "").replace("_", " ").title()
                
                # Format the text with the source tag
                formatted_text = f"[SOURCE: {source_name}]\n{item.content}"
                context_data.append(formatted_text)

                # Log for debugging
                preview = item.content[:100].replace('\n', ' ')
                print(f"   Result #{i+1} ({source_name}): \"{preview}...\"")
        else:
            print("⚠️ [RAG] No relevant documents found.")
        
        return context_data