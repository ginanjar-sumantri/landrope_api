from models.spk_model import SpkBase, SpkFullBase
from common.partial import optional
from schemas.bidang_sch import BidangForSPKById
from schemas.spk_beban_biaya_sch import SpkBebanBiayaCreateExtSch, SpkBebanBiayaSch, SpkBebanBiayaUpdateExtSch
from schemas.spk_kelengkapan_dokumen_sch import SpkKelengkapanDokumenCreateExtSch, SpkKelengkapanDokumenSch, SpkKelengkapanDokumenUpdateExtSch
from common.enum import HasilAnalisaPetaLokasiEnum
from sqlmodel import Field


class SpkCreateSch(SpkBase):
    spk_beban_biayas:list[SpkBebanBiayaCreateExtSch] | None
    spk_kelengkapan_dokumens:list[SpkKelengkapanDokumenCreateExtSch] | None

class SpkSch(SpkFullBase):
    id_bidang:str | None = Field(alias="id_bidang")
    alashak:str | None = Field(alias="alashak")
    hasil_analisa_peta_lokasi:HasilAnalisaPetaLokasiEnum | None = Field(alias="hasil_analisa_peta_lokasi")
    kjb_hd_code:str | None = Field(alias="kjb_hd_code")

class SpkByIdSch(SpkFullBase):
    bidang:BidangForSPKById | None

    spk_beban_biayas:list[SpkBebanBiayaSch] | None
    spk_kelengkapan_dokumens:list[SpkKelengkapanDokumenSch] | None

@optional
class SpkUpdateSch(SpkBase):
    spk_beban_biayas:list[SpkBebanBiayaUpdateExtSch] | None
    spk_kelengkapan_dokumens:list[SpkKelengkapanDokumenUpdateExtSch] | None