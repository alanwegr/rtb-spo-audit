"""Pydantic models for OpenRTB SupplyChain object v1.0."""
from pydantic import BaseModel, Field


class SupplyChainNode(BaseModel):
    asi: str = Field(..., description="Ad System Identifier, e.g. 'google.com'")
    sid: str = Field(..., description="Seller ID within the ad system")
    rid: str = Field(..., description="Request ID (route through)")
    name: str | None = None
    domain: str | None = None
    hp: int = Field(default=1, description="Hop count")


class SupplyChain(BaseModel):
    ver: str = "1.0"
    complete: int = 1
    nodes: list[SupplyChainNode]
    ext: dict | None = None
