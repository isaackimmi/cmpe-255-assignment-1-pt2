"""Typed transport contracts for the public API."""
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    data_source: str


class Transaction(BaseModel):
    transaction_id: str
    items: list[str]


class TransactionsResponse(BaseModel):
    rows: list[Transaction]


class Itemset(BaseModel):
    items: list[str]
    label: str
    support: float = Field(ge=0, le=1)
    count: int = Field(ge=1)
    size: int = Field(ge=1)


class ItemsetsResponse(BaseModel):
    rows: list[Itemset]
    transaction_count: int
    effective_count: int


class Rule(BaseModel):
    antecedent: list[str]
    consequent: list[str]
    label: str
    support: float
    support_count: int
    antecedent_count: int
    consequent_count: int
    confidence: float
    lift: float


class RulesResponse(BaseModel):
    rows: list[Rule]
    transaction_count: int


class ContextCandidate(BaseModel):
    item: str
    count: int
    conditional_probability: float


class ContextResponse(BaseModel):
    item: str
    basket_count: int
    candidates: list[ContextCandidate]
    interpretation: str
