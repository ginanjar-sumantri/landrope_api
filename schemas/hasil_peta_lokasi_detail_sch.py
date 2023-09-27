from models.hasil_peta_lokasi_model import HasilPetaLokasiDetailBase, HasilPetaLokasiDetailFullBase
from common.partial import optional
from common.as_form import as_form
from common.enum import TipeOverlapEnum, StatusLuasOverlapEnum
from sqlmodel import SQLModel, Field
from typing import Optional
from uuid import UUID
from decimal import Decimal

class HasilPetaLokasiDetailCreateSch(HasilPetaLokasiDetailBase):
    pass

class HasilPetaLokasiDetailCreateExtSch(SQLModel):
    tipe_overlap:TipeOverlapEnum
    bidang_id:UUID | None
    luas_overlap:Decimal | None 
    keterangan:str | None 
    draft_detail_id:UUID | None
    status_luas:StatusLuasOverlapEnum | None

class HasilPetaLokasiDetailSch(HasilPetaLokasiDetailFullBase):
    id_bidang:str|None = Field(alias="id_bidang")
    alashak:str|None = Field(alias="alashak")

@optional
class HasilPetaLokasiDetailUpdateSch(HasilPetaLokasiDetailBase):
    pass

class HasilPetaLokasiDetailForUtj(SQLModel):
    id:Optional[UUID]
    keterangan:Optional[str]

# @optional
# class HasilPetaLokasiDetailUpdateExtSch(SQLModel):
#     id:UUID | None
#     tipe_overlap:TipeOverlapEnum
#     bidang_id:UUID | None
#     luas_overlap:Decimal | None 
#     keterangan:str | None 
#     draft_detail_id:UUID | None
#     bidang_overlap_id:UUID | None
