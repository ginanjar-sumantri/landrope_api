from sqlmodel import SQLModel, Field, Relationship
from models.peminjaman_header_model import PeminjamanHeaderBase, PeminjamanHeaderFullBase
from schemas.peminjaman_bidang_sch import PeminjamanBidangCreateUpdateSch, PeminjamanBidangSch
from schemas.peminjaman_penggarap_sch import PeminjamanPenggarapCreateSch, PeminjamanPenggarapSch
from common.enum import KategoriTipeTanahEnum
from uuid import UUID
from decimal import Decimal


class PeminjamanHeaderCreateSch(PeminjamanHeaderBase):
    peminjaman_bidangs: list[UUID]

class PeminjamanHeaderSch(PeminjamanHeaderBase):
    project_name: str | None
    desa_name: str | None
    ptsk_name: str | None
  
    
class PeminjamanHeaderByIdSch(PeminjamanHeaderFullBase):
    project_name: str | None
    desa_name: str | None
    ptsk_name: str | None

    peminjaman_bidangs: list[PeminjamanBidangSch] | None 
    peminjaman_penggaraps: list[PeminjamanPenggarapSch] | None 


class PeminjamanHeaderEditSch(PeminjamanHeaderBase):
    peminjaman_bidangs: list[UUID] 

class PeminjamanHeaderUpdateSch(SQLModel):
    peminjaman_penggaraps: list[PeminjamanPenggarapCreateSch] | None 


class BidangSearchListSch(SQLModel):
    id: UUID
    alashak: str | None
    pemilik_name: str | None
    group: str | None
    luas_bayar: Decimal | None