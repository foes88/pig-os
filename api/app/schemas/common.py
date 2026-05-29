from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard envelope for all success responses."""
    data: T
    meta: dict | None = None


class PageMeta(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int


class PagedResponse(BaseModel, Generic[T]):
    items: list[T]
    meta: PageMeta


class OrmBase(BaseModel):
    """Base for models that read from ORM objects."""
    model_config = ConfigDict(from_attributes=True)


class UUIDMixin(OrmBase):
    id: UUID
