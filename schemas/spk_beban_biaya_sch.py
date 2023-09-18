from models.spk_model import SpkBebanBiayaBase, SpkBebanBiayaFullBase
from common.partial import optional
from schemas.bidang_sch import BidangForSPKByIdSch
from common.enum import HasilAnalisaPetaLokasiEnum
from sqlmodel import Field, SQLModel
from uuid import UUID


class SpkBebanBiayaCreateSch(SpkBebanBiayaBase):
    pass

class SpkBebanBiayaCreateExtSch(SQLModel):
    beban_biaya_id:UUID | None
    beban_pembeli:bool | None

class SpkBebanBiayaSch(SpkBebanBiayaFullBase):
    beban_biaya_name:str | None = Field(alias="beban_biaya_name")

class SpkBebanBiayaByIdSch(SpkBebanBiayaFullBase):
    pass

@optional
class SpkBebanBiayaUpdateSch(SpkBebanBiayaBase):
    pass


@optional
class SpkBebanBiayaUpdateExtSch(SpkBebanBiayaBase):
    id:UUID | None