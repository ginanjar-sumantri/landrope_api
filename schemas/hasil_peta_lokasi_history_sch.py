from models.hasil_peta_lokasi_model import HasilPetaLokasiHistoryBaseExt, HasilPetaLokasiHistoryFullBase
from common.partial import optional
from sqlmodel import Field, SQLModel
from uuid import UUID

class HasilPetaLokasiHistoryCreateSch(HasilPetaLokasiHistoryBaseExt):
    pass

class HasilPetaLokasiHistorySch(HasilPetaLokasiHistoryFullBase):
    trans_worker_name:str|None = Field(alias="trans_worker_name")