"""
Enhanced Knowledge Service for RAG

Improvements:
- Query expansion with astrology synonyms
- Score threshold filtering
- Better logging and quality metrics
- Keyword extraction for hybrid context
"""

from typing import List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.persistence.repositories.knowledge_repo import KnowledgeRepository
from app.ai.llm_client import LLMClient


class KnowledgeService:
    """
    Enhanced knowledge service with:
    - Astrology-aware query expansion
    - Score-based filtering
    - Quality logging
    """

    # Astrology-specific synonyms for query expansion
    ASTROLOGY_SYNONYMS = {
        "career": ["profession", "job", "work", "10th house", "dasham bhava", "karma sthana"],
        "marriage": ["spouse", "partner", "wife", "husband", "7th house", "vivah", "kalatra"],
        "health": ["disease", "illness", "body", "6th house", "rog", "arogya"],
        "money": ["wealth", "finance", "income", "2nd house", "dhana", "lakshmi"],
        "children": ["progeny", "son", "daughter", "5th house", "putra", "santan"],
        "education": ["learning", "study", "knowledge", "4th house", "vidya"],
        "love": ["romance", "affair", "5th house", "prem"],
        "saturn": ["shani", "sade sati", "saturn return"],
        "jupiter": ["guru", "brihaspati"],
        "mars": ["mangal", "kuja", "manglik"],
        "venus": ["shukra"],
        "mercury": ["budh"],
        "sun": ["surya", "ravi"],
        "moon": ["chandra", "soma"],
        "rahu": ["north node", "dragon's head"],
        "ketu": ["south node", "dragon's tail"],
        "dasha": ["mahadasha", "antardasha", "planetary period"],
        "yoga": ["raj yoga", "dhana yoga", "vipreet"],
        "dosha": ["mangal dosha", "kaal sarpa dosha", "pitra dosha"],
    }

    # Distance thresholds for L2 distance (text-embedding-3-small)
    DISTANCE_EXCELLENT = 0.6   # Very relevant
    DISTANCE_GOOD = 0.9        # Relevant
    DISTANCE_ACCEPTABLE = 1.2  # May be useful
    DISTANCE_MAX = 1.5         # Cutoff

    def __init__(self):
        self.llm_client = LLMClient()

    async def retrieve_context(
        self, 
        session: AsyncSession, 
        query: str, 
        limit: int = 5,
        use_expansion: bool = True,
        threshold: float = 1.2,
    ) -> List[str]:
        """
        Enhanced RAG retrieval with:
        - Query expansion for better recall
        - Score threshold for quality filtering
        - Detailed logging for debugging
        """
        print(f"\n🔎 [RAG] Searching knowledge for: '{query}'")

        # 1. Infer Category & Expand Query
        category = self._infer_category(query)
        expanded_terms = self._expand_query(query) if use_expansion else [query]
        
        if category:
            print(f"   🔖 Inferred Category: {category.upper()}")
        if len(expanded_terms) > 1:
            print(f"   📚 Expanded to: {expanded_terms}")

        # 2. Get embedding for the original query
        query_vector = await self.llm_client.get_embedding(query)

        # 3. Search with distances
        repo = KnowledgeRepository(session)
        
        # Try specific category filter first if confident
        if category:
            results = await repo.search_with_distances(
                query_vector, 
                limit=limit * 2, 
                filter_category=category
            )
            if not results:
                print("   ⚠️ No results in category, falling back to global search.")
                results = await repo.search_with_distances(query_vector, limit=limit * 2)
        else:
            results = await repo.search_with_distances(query_vector, limit=limit * 2)

        # 4. Filter by threshold
        filtered = [(item, dist) for item, dist in results if dist < threshold]
        
        # 5. Log quality metrics
        self._log_retrieval_quality(results, filtered, threshold)

        # 6. Build structured sources
        sources = []
        for idx, (item, distance) in enumerate(filtered[:limit], start=1):
            raw_source = item.metadata_info or "Unknown Source"
            source_name = raw_source.replace(".txt", "").replace(".pdf", "").replace("_", " ").title()
            quality = self._distance_to_quality(distance)
            
            sources.append({
                "id": idx,
                "source": source_name,
                "content": item.content,
                "relevance": quality,
            })
            
            preview = item.content[:80].replace('\n', ' ')
            print(f"   ✓ [{quality}] {source_name}: \"{preview}...\"")

        if not sources:
            print("⚠️ [RAG] No relevant documents found above threshold. Strict mode active - returning empty context.")
            # Strict mode: Do not return low confidence chunks
            self._last_sources = []
            return []

        # Store sources for later retrieval
        self._last_sources = sources
        
        # 7. Return formatted text for backward compatibility
        context_data = [
            f"[SOURCE: {s['source']}] [Relevance: {s['relevance']}]\n{s['content']}"
            for s in sources
        ]
        return context_data

    def get_last_sources(self) -> List[Dict[str, Any]]:
        """Return structured sources from the last retrieval."""
        return getattr(self, '_last_sources', [])

    def _expand_query(self, query: str) -> List[str]:
        """
        Expand query with astrology-specific synonyms.
        """
        expanded = [query]
        query_lower = query.lower()
        
        for term, synonyms in self.ASTROLOGY_SYNONYMS.items():
            if term in query_lower:
                # Add the first 2 most relevant synonyms
                expanded.extend(synonyms[:2])
        
        return list(set(expanded))[:5]  # Limit expansion

    def _infer_category(self, query: str) -> str | None:
        """
        Simple heuristic to map query to Vedic categories.
        """
        q = query.lower()
        
        # Artha (Career/Money)
        if any(w in q for w in ["job", "career", "money", "wealth", "business", "promotion", "finance", "income"]):
            return "artha"
            
        # Kama (Love/Marriage)
        if any(w in q for w in ["love", "marriage", "wife", "husband", "spouse", "relationship", "affair", "partner"]):
            return "kama"
            
        # Health
        if any(w in q for w in ["health", "disease", "illness", "sick", "pain", "medical", "surgery"]):
            return "health"
            
        # Moksha
        if any(w in q for w in ["liberation", "death", "loss", "spiritual", "moksha", "enlightenment"]):
            return "moksha"
            
        # Dharma (General/Duty)
        if any(w in q for w in ["property", "home", "mother", "father", "duty", "righteousness"]):
            # Note: "Dharma" is broad, could be "general"
            return "dharma"
            
        return None

    def _distance_to_quality(self, distance: float) -> str:
        """Convert L2 distance to human-readable quality."""
        if distance < self.DISTANCE_EXCELLENT:
            return "Excellent"
        elif distance < self.DISTANCE_GOOD:
            return "Good"
        elif distance < self.DISTANCE_ACCEPTABLE:
            return "Fair"
        else:
            return "Low"

    def _log_retrieval_quality(
        self, 
        all_results: List[Tuple], 
        filtered: List[Tuple],
        threshold: float
    ):
        """Log detailed quality metrics."""
        if not all_results:
            print("   ℹ️ No results from database")
            return
        
        distances = [dist for _, dist in all_results]
        best = min(distances)
        worst = max(distances)
        avg = sum(distances) / len(distances)
        
        print(f"   📊 Quality: Best={best:.2f}, Avg={avg:.2f}, Worst={worst:.2f}")
        print(f"   ✅ {len(filtered)}/{len(all_results)} passed threshold ({threshold})")

    def extract_keywords(self, query: str) -> List[str]:
        """
        Extract important keywords from query for hybrid retrieval.
        Useful for passing to the LLM alongside RAG context.
        """
        # Simple keyword extraction (no external dependencies)
        stopwords = {"what", "is", "my", "the", "a", "an", "in", "for", "to", "of", "about", "tell", "me", "can", "you", "will", "be", "should", "i", "how", "when", "where", "why"}
        
        words = query.lower().split()
        keywords = [w.strip("?.,!") for w in words if w.lower() not in stopwords and len(w) > 2]
        
        # Add expanded terms
        for term in keywords.copy():
            if term in self.ASTROLOGY_SYNONYMS:
                keywords.extend(self.ASTROLOGY_SYNONYMS[term][:1])
        
        return list(set(keywords))