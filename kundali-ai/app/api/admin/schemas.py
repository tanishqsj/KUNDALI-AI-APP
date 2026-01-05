from pydantic import BaseModel, Field
from typing import Dict, Any
from uuid import UUID


class RuleCreateRequest(BaseModel):
    rule_key: str
    category: str
    conditions: Dict[str, Any]
    effects: Dict[str, Any]


class RuleResponse(BaseModel):
    id: UUID
    rule_key: str
    category: str
    is_active: bool
