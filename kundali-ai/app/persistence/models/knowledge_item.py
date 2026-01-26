from sqlalchemy import Column, Integer, String, Text, Index
from pgvector.sqlalchemy import Vector
from app.persistence.base import Base

class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    metadata_info = Column(String, nullable=True)  # e.g. "BPHS Chapter 4"
    category = Column(String, nullable=True, index=True)  # e.g. "career", "health"
    keywords = Column(String, nullable=True) # e.g. "job, promotion, saturn"
    # Add HNSW index configuration
    embedding = Column(Vector(1536))
    
    __table_args__ = (
        Index(
            'ix_knowledge_items_embedding',
            'embedding',
            postgresql_using='hnsw',
            postgresql_with={'m': 16, 'ef_construction': 64},
            postgresql_ops={'embedding': 'vector_l2_ops'}
        ),
    )