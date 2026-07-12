from pydantic import BaseModel, ConfigDict


class UniversityConfig(BaseModel):
    """Configuration schema for a single university."""
    
    slug: str
    name: str
    locale: str
    domain: str
    qdrant_collection: str
    sources: list[str]

    model_config = ConfigDict(
        frozen=True,
    )
