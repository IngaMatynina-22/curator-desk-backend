from pydantic import BaseModel, Field


class IntegrityIssue(BaseModel):
    code: str
    severity: str = "warning"
    message: str
    entity_type: str | None = None
    entity_id: int | None = None


class IntegrityReport(BaseModel):
    ok: bool
    issues: list[IntegrityIssue] = Field(default_factory=list)

    @property
    def issue_count(self) -> int:
        return len(self.issues)
