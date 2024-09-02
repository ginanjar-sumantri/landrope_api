from sqlmodel import SQLModel
from models.pelepasan_header_model import PelepasanHeaderBase, PelepasanHeaderFullBase
from schemas.pelepasan_bidang_sch import PelepasanBidangCreateUpdateSch, PelepasanBidangSch
from common.partial import optional
from common.as_form import as_form
from uuid import UUID
from decimal import Decimal

class PelepasanHeaderCreateSch(PelepasanHeaderBase):
    pelepasan_bidangs: list[UUID]


class PelepasanHeaderSch(PelepasanHeaderFullBase):
    project_name: str | None
    desa_name: str | None
    ptsk_name: str | None
    jenis_surat_name: str | None
    total_luas_bayar: Decimal | None

class PelepasanHeaderByIdSch(PelepasanHeaderFullBase):
    project_name: str | None
    desa_name: str | None
    ptsk_name: str | None
    jenis_surat_name: str | None
    total_luas_bayar: Decimal | None

    pelepasan_bidangs: list[PelepasanBidangSch]

class PelepasanHeaderEditSch(PelepasanHeaderBase):
    pelepasan_bidangs: list[UUID]

@as_form
class PelepasanHeaderUpdateSch(PelepasanHeaderBase):
    pass

class BidangSearchSch(SQLModel):
    id: UUID
    alashak: str | None
    pemilik_name: str | None
    group: str | None
    luas_bayar: Decimal | None