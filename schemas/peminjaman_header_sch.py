from sqlmodel import SQLModel, Field, Relationship
from models.peminjaman_header_model import PeminjamanHeaderBase, PeminjamanHeaderFullBase
from models.peminjaman_bidang_model import PeminjamanBidangBase
from schemas.peminjaman_bidang_sch import PeminjamanBidangCreateUpdateSch, PeminjamanBidangSch
from common.as_form import as_form

class PeminjamanHeaderCreateSch(PeminjamanHeaderBase):
    peminjaman_bidangs: list[PeminjamanBidangCreateUpdateSch]


class PeminjamanHeaderSch(PeminjamanHeaderFullBase):
    project_name: str | None
    desa_name: str | None
    ptsk_name: str | None

class PeminjamanHeaderByIdSch(PeminjamanHeaderFullBase):
    project_name: str | None
    desa_name: str | None
    ptsk_name: str | None

    peminjaman_bidangs: list[PeminjamanBidangSch]

class PeminjamanHeaderEditSch(PeminjamanHeaderBase):
    peminjaman_bidangs: list[PeminjamanBidangCreateUpdateSch] | None 

@as_form
class PeminjamanHeaderUpdateSch(PeminjamanHeaderBase):
    pass

