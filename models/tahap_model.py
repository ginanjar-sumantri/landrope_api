from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING, Optional
from decimal import Decimal

if TYPE_CHECKING:
    from planing_model import Planing
    from ptsk_model import Ptsk
    from bidang_model import Bidang
    from worker_model import Worker

class TahapBase(SQLModel):
    nomor_tahap:Optional[int] = Field(nullable=False)
    planing_id:UUID = Field(foreign_key="planing.id", nullable=False)
    ptsk_id:Optional[UUID] = Field(foreign_key="ptsk.id", nullable=True)
    group:Optional[str] = Field(nullable=True)

class TahapFullBase(BaseUUIDModel, TahapBase):
    pass

class Tahap(TahapFullBase, table=True):
    details: "TahapDetail" = Relationship(back_populates="tahap",
                                           sa_relationship_kwargs=
                                           {
                                               "lazy" : "selectin"
                                           })

    planing:"Planing" = Relationship(sa_relationship_kwargs=
                                     {
                                        "lazy" : "selectin"
                                     })
    ptsk:"Ptsk" = Relationship(sa_relationship_kwargs=
                                     {
                                        "lazy" : "selectin"
                                     })
    
    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "Tahap.updated_by_id==Worker.id",
        }
    )

    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)
    
    @property
    def ptsk_name(self) -> str | None:
        return getattr(getattr(self, 'ptsk', None), 'name', None)
    
    @property
    def project_name(self) -> str | None:
        return getattr(getattr(getattr(self, 'planing', None), 'project', None), "name", None)
    
    @property
    def desa_name(self) -> str | None:
        return getattr(getattr(getattr(self, 'planing', None), 'desa', None), "name", None)
    
    @property
    def planing_name(self) -> str | None:
        return getattr(getattr(self, 'planing', None), 'name', None)
    
    @property
    def jumlah_bidang(self) -> int | None:
        jumlah = len(self.details)

        return jumlah or 0
    
    
    
class TahapDetailBase(SQLModel):
    tahap_id:UUID = Field(foreign_key="tahap.id", nullable=False)
    bidang_id:UUID = Field(foreign_key="bidang.id", nullable=False)
    is_void:bool = Field(nullable=False, default=False)
    remark:Optional[str] = Field(nullable=True)

class TahapDetailFullBase(BaseUUIDModel, TahapDetailBase):
    pass

class TahapDetail(TahapDetailFullBase, table=True):
    tahap:"Tahap" = Relationship(back_populates="details",
                                sa_relationship_kwargs=
                                     {
                                        "lazy" : "selectin"
                                     })
    
    bidang:"Bidang" = Relationship(sa_relationship_kwargs=
                                     {
                                        "lazy" : "selectin"
                                     })
    

    @property
    def id_bidang(self) -> str | None:
        return getattr(getattr(self, "bidang", None), "id_bidang", None)
    
    @property
    def luas_surat(self) -> Decimal | None:
        return getattr(getattr(self, "bidang", None), "luas_surat", None)
    
    @property
    def luas_ukur(self) -> Decimal | None:
        return getattr(getattr(self, "bidang", None), "luas_ukur", None)
    
    @property
    def luas_gu_perorangan(self) -> Decimal | None:
        return getattr(getattr(self, "bidang", None), "luas_gu_perorangan", None)
    
    @property
    def luas_gu_pt(self) -> Decimal | None:
        return getattr(getattr(self, "bidang", None), "luas_gu_pt", None)
    
    @property
    def luas_nett(self) -> Decimal | None:
        return getattr(getattr(self, "bidang", None), "luas_nett", None)
    
    @property
    def luas_clear(self) -> Decimal | None:
        return getattr(getattr(self, "bidang", None), "luas_clear", None)
    
    @property
    def luas_pbt_perorangan(self) -> Decimal | None:
        return getattr(getattr(self, "bidang", None), "luas_pbt_perorangan", None)
    
    @property
    def luas_pbt_pt(self) -> Decimal | None:
        return getattr(getattr(self, "bidang", None), "luas_pbt_pt", None)
    
    @property
    def luas_bayar(self) -> Decimal | None:
        return getattr(getattr(self, "bidang", None), "luas_bayar", None)
    
    @property
    def satuan(self) -> Decimal | None:
        return getattr(getattr(self, "bidang", None), "satuan", None)
    
    @property
    def satuan_akta(self) -> Decimal | None:
        return getattr(getattr(self, "bidang", None), "satuan_akta", None)
    
    @property
    def project_name(self) -> str | None:
        return getattr(getattr(self, "bidang", None), "project_name", None)
    
    @property
    def desa_name(self) -> str | None:
        return getattr(getattr(self, "bidang", None), "desa_name", None)
    
    @property
    def planing_name(self) -> str | None:
        return getattr(getattr(self, "bidang", None), "planing_name", None)
    
    @property
    def ptsk_name(self) -> str | None:
        return getattr(getattr(self, "bidang", None), "ptsk_name", None)
    
    @property
    def harga_total(self) -> Decimal | None:
        return (self.bidang.harga_transaksi or 0) * (self.bidang.luas_bayar or 0)

        
    
