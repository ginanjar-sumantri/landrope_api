from sqlmodel import SQLModel, Field, Relationship, Column
from models.base_model import BaseUUIDModel, BaseGeoModel
from uuid import UUID
from typing import TYPE_CHECKING
from decimal import Decimal
from common.enum import StatusLuasOverlapEnum, KategoriOverlapEnum
from geoalchemy2 import Geometry

if TYPE_CHECKING:
    from models import Bidang, HasilPetaLokasiDetail

class BidangOverlapBase(SQLModel):
    code:str | None
    parent_bidang_id:UUID | None = Field(foreign_key="bidang.id")
    parent_bidang_intersect_id:UUID | None = Field(foreign_key="bidang.id")
    luas:Decimal | None
    luas_bayar:Decimal | None = Field(nullable=True)
    status_luas:StatusLuasOverlapEnum | None = Field(nullable=True)
    kategori:KategoriOverlapEnum | None = Field(nullable=True)
    harga_transaksi:Decimal | None = Field(nullable=True)
    is_show:bool|None = Field(nullable=True) #show di printout atau engga

class BidangOverlapRawBase(BaseUUIDModel, BidangOverlapBase):
    pass

class BidangOverlapFullBase(BaseGeoModel, BidangOverlapRawBase):
    geom_temp:str | None = Field(sa_column=Column(Geometry))

class BidangOverlap(BidangOverlapFullBase, table=True):
    bidang:"Bidang" = Relationship(
                            sa_relationship_kwargs=
                            {
                                "lazy" : "joined",
                                "primaryjoin": "BidangOverlap.parent_bidang_id==Bidang.id"
                            }
    )

    bidang_intersect:"Bidang" = Relationship(
                            sa_relationship_kwargs=
                            {
                                "lazy" : "joined",
                                "primaryjoin": "BidangOverlap.parent_bidang_intersect_id==Bidang.id"
                            }
    )

    hasil_peta_lokasi_detail:"HasilPetaLokasiDetail" = Relationship(
        back_populates="bidang_overlap",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )


    @property
    def id_bidang_parent(self) -> str | None :
        return getattr(getattr(self, "bidang", None), "id_bidang", None)
    
    @property
    def id_bidang_intersect(self) -> str | None :
        return getattr(getattr(self, "bidang_intersect", None), "id_bidang", None)
    
    @property
    def alashak_parent(self) -> str | None :
        return getattr(getattr(self, "bidang", None), "alashak", None)
    
    @property
    def alashak_intersect(self) -> str | None :
        return getattr(getattr(self, "bidang_intersect", None), "alashak", None)
    
    @property
    def jenis_bidang_intersect(self) -> str | None :
        return getattr(getattr(self, "bidang_intersect", None), "jenis_bidang", None)
    
    @property
    def tipe_overlap(self) -> str | None :
        return getattr(getattr(self, "hasil_peta_lokasi_detail", None), "tipe_overlap", None)
    
    @property
    def luas_surat_parent(self) -> str | None :
        return getattr(getattr(self, "bidang", None), "luas_surat", None)
    
    @property
    def luas_surat_intersect(self) -> str | None :
        return getattr(getattr(self, "bidang_intersect", None), "luas_surat", None)