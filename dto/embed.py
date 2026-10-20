from pydantic import BaseModel, Field


class EmbedRequest(BaseModel):
    sourceKey: str | None = Field(
        default=None,
        description="Optional knowledge file stem (e.g. services). Omit to reindex all.",
    )


class EmbedAcceptedResponse(BaseModel):
    accepted: bool = True
    sourceKey: str | None = None
