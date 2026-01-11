from sqlalchemy import Column, Integer, String, Text
from pgvector.sqlalchemy import Vector
from app.persistence.base import Base

class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    metadata_info = Column(String, nullable=True)  # e.g. "BPHS Chapter 4"
    embedding = Column(Vector(1536))  # Matches OpenAI's text-embedding-3-small