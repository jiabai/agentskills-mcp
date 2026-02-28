from typing import Generic, TypeVar

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str
    code: str
    timestamp: str


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
