from sqlmodel import SQLModel
from models.pelepasan_header_model import PelepasanHeaderBase, PelepasanHeaderFullBase
from schemas.pelepasan_bidang_sch import PelepasanBidangCreateUpdateSch, PelepasanBidangSch
from common.partial import optional
from common.as_form import as_form

class PelepasanHeaderCreateSch(PelepasanHeaderBase):
    pelepasan_bidangs: list[PelepasanBidangCreateUpdateSch]


class PelepasanHeaderSch(PelepasanHeaderFullBase):
    project_name: str | None
    desa_name: str | None
    ptsk_name: str | None
    jenis_surat_name: str | None

class PelepasanHeaderByIdSch(PelepasanHeaderFullBase):
    project_name: str | None
    desa_name: str | None
    ptsk_name: str | None
    jenis_surat_name: str | None

    pelepasan_bidangs: list[PelepasanBidangSch]

class PelepasanHeaderEditSch(PelepasanHeaderBase):
    pelepasan_bidangs: list[PelepasanBidangCreateUpdateSch]

@as_form
class PelepasanHeaderUpdateSch(PelepasanHeaderBase):
    pass