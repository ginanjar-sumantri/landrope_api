from models.spk_model import SpkBase, SpkFullBase
from common.partial import optional
from common.enum import HasilAnalisaPetaLokasiEnum
from sqlmodel import Field


class SpkCreateSch(SpkBase):
    pass

class SpkSch(SpkFullBase):
    id_bidang:str | None = Field(alias="id_bidang")
    alashak:str | None = Field(alias="alashak")
    hasil_analisa_peta_lokasi:HasilAnalisaPetaLokasiEnum | None = Field(alias="hasil_analisa_peta_lokasi")
    kjb_hd_code:str | None = Field(alias="kjb_hd_code")

@optional
class SpkUpdateSch(SpkBase):
    pass