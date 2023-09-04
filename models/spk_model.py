from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, String
from models.base_model import BaseUUIDModel
from common.enum import JenisBayarEnum, HasilAnalisaPetaLokasiEnum, SatuanBayarEnum
from uuid import UUID
from pydantic import condecimal
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from models.bidang_model import Bidang
    from models.kjb_model import KjbTermin

class SpkBase(SQLModel):
    bidang_id:UUID = Field(foreign_key="bidang.id", nullable=False)
    jenis_bayar:Optional[JenisBayarEnum] = Field(nullable=True)
    nilai:condecimal(decimal_places=2) = Field(default=0)
    satuan_bayar:SatuanBayarEnum | None = Field(nullable=True)

class SpkFullBase(BaseUUIDModel, SpkBase):
    pass

class Spk(SpkFullBase, table=True):
    bidang:"Bidang" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "selectin",

        }
    )

    @property
    def id_bidang(self) -> str | None:
        return self.bidang.id_bidang
    
    @property
    def alashak(self) -> str | None:
        return self.bidang.alashak
    
    @property
    def hasil_analisa_peta_lokasi(self) -> HasilAnalisaPetaLokasiEnum | None:
        return self.bidang.hasil_peta_lokasi.hasil_analisa_peta_lokasi
    
    @property
    def kjb_hd_code(self) -> str | None:
        return self.bidang.hasil_peta_lokasi.kjb_dt.kjb_code
    
