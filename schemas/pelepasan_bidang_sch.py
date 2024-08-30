from sqlmodel import SQLModel
from models.pelepasan_bidang_model import PelepasanBidangBase, PelepasanBidangFullBase
from common.partial import optional
from uuid import UUID
from decimal import Decimal

class PelepasanBidangCreateSch(PelepasanBidangBase):
    pass

class PelepasanBidangSch(PelepasanBidangFullBase):
    id_bidang: str | None
    alashak: str | None
    pemilik_name: str | None
    group: str | None
    luas_bayar: Decimal | None

class PelepasanBidangUpdateSch(PelepasanBidangBase):
    pass

class PelepasanBidangCreateUpdateSch(PelepasanBidangBase):
    id: UUID | None