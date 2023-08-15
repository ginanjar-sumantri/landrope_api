from models.hasil_peta_lokasi_model import HasilPetaLokasiDetailBase, HasilPetaLokasiFullBase
from common.partial import optional
from common.as_form import as_form
from common.enum import TipeOverlapEnum
from sqlmodel import SQLModel, Field
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

class HasilPetaLokasiDetailSch(HasilPetaLokasiFullBase):
    pass

@optional
class HasilPetaLokasiDetailUpdateSch(HasilPetaLokasiDetailBase):
    pass