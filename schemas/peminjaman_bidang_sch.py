from sqlmodel import SQLModel
from models.peminjaman_bidang_model import PeminjamanBidangBase, PeminjamanBidangFullBase
from common.partial import optional
from uuid import UUID
from decimal import Decimal

class PeminjamanBidangCreateSch(PeminjamanBidangBase):
    pass

class PeminjamanBidangSch(PeminjamanBidangFullBase):
    id_bidang: str | None
    alashak: str | None
    pemilik_name: str | None
    group: str | None
    luas_bayar: Decimal | None

class PeminjamanBidangUpdateSch(PeminjamanBidangBase):
    pass

class PeminjamanBidangCreateUpdateSch(PeminjamanBidangBase):
    id: UUID | None