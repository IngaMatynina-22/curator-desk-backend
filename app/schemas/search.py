from pydantic import BaseModel, Field


class GlobalSearchQuery(BaseModel):
    query: str = Field(..., min_length=1)
    offset: int = 0
    limit: int = 20


class SearchHit(BaseModel):
    entity_type: str
    entity_id: int
    title: str
    snippet: str | None = None


class GlobalSearchResult(BaseModel):
    students: list[SearchHit] = Field(default_factory=list)
    events: list[SearchHit] = Field(default_factory=list)
    notes: list[SearchHit] = Field(default_factory=list)
    curator_logs: list[SearchHit] = Field(default_factory=list)
