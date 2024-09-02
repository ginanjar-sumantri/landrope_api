from sqlmodel import SQLModel, Field, Relationship
from models.peminjaman_header_model import PeminjamanHeaderBase, PeminjamanHeaderFullBase
from schemas.peminjaman_bidang_sch import PeminjamanBidangCreateUpdateSch, PeminjamanBidangSch
from schemas.peminjaman_penggarap_sch import PeminjamanPenggarapCreateSch
from common.as_form import as_form
from uuid import UUID

class PeminjamanHeaderCreateSch(PeminjamanHeaderBase):
    peminjaman_bidangs: list[UUID]

class PeminjamanHeaderSch(PeminjamanHeaderFullBase):
    project_name: str | None
    desa_name: str | None
    ptsk_name: str | None

class PeminjamanHeaderByIdSch(PeminjamanHeaderFullBase):
    project_name: str | None
    desa_name: str | None
    ptsk_name: str | None

    peminjaman_bidangs: list[PeminjamanBidangSch] | None 

class PeminjamanHeaderEditSch(PeminjamanHeaderBase):
    peminjaman_bidangs: list[UUID] 

class PeminjamanHeaderUpdateSch(SQLModel):
    peminjaman_penggaraps: list[PeminjamanPenggarapCreateSch] | None 
