"""OpenRTB 2.5/3.0 bid request/response models. Strict, no extras ignored."""
from pydantic import BaseModel, Field
from models.schain import SupplyChain


class Imp(BaseModel):
    id: str
    bidfloor: float = 0.0
    bidfloorcur: str = "USD"


class Site(BaseModel):
    id: str | None = None
    domain: str
    publisher: dict | None = None


class Source(BaseModel):
    fd: int | None = None
    tid: str | None = None
    ext: dict | None = None  # contains schain


class BidRequest(BaseModel):
    id: str
    imp: list[Imp]
    site: Site | None = None
    app: dict | None = None
    source: Source | None = None
    tmax: int | None = None
    at: int = 2  # 2=second-price, 1=first-price


class SeatBid(BaseModel):
    seat: str
    bid: list["Bid"]


class Bid(BaseModel):
    id: str
    impid: str
    price: float
    adid: str | None = None
    adm: str | None = None
    nurl: str | None = None


class BidResponse(BaseModel):
    id: str
    seatbid: list[SeatBid]
    cur: str = "USD"


Bid.model_rebuild()
SeatBid.model_rebuild()
