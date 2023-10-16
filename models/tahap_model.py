from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from models import BidangOverlap
from common.enum import JenisBayarEnum
from uuid import UUID
from typing import TYPE_CHECKING, Optional
from decimal import Decimal

if TYPE_CHECKING:
    from models import Planing, Ptsk, Bidang, Worker, SubProject, Termin

class TahapBase(SQLModel):
    nomor_tahap:Optional[int] = Field(nullable=False)
    planing_id:UUID = Field(foreign_key="planing.id", nullable=False)
    ptsk_id:Optional[UUID] = Field(foreign_key="ptsk.id", nullable=True)
    sub_project_id:Optional[UUID] = Field(foreign_key="sub_project.id")
    group:Optional[str] = Field(nullable=True)

class TahapFullBase(BaseUUIDModel, TahapBase):
    pass

class Tahap(TahapFullBase, table=True):
    details: list["TahapDetail"] = Relationship(back_populates="tahap",
                                           sa_relationship_kwargs=
                                           {
                                               "lazy" : "select"
                                           })
    
    termins: list["Termin"] = Relationship(
        back_populates="tahap",
        sa_relationship_kwargs=
        {
            'lazy' : 'select'
        }
    )

    planing:"Planing" = Relationship(sa_relationship_kwargs=
                                     {
                                        "lazy" : "select"
                                     })
    ptsk:"Ptsk" = Relationship(sa_relationship_kwargs=
                                     {
                                        "lazy" : "select"
                                     })
    
    sub_project:"SubProject" = Relationship(sa_relationship_kwargs=
                                     {
                                        "lazy" : "select"
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
    def section_name(self) -> str | None:
        return getattr(getattr(getattr(getattr(self, 'planing', None), 'project', None), "section", None), "name", None)
    
    @property
    def desa_name(self) -> str | None:
        return getattr(getattr(getattr(self, 'planing', None), 'desa', None), "name", None)
    
    @property
    def planing_name(self) -> str | None:
        return getattr(getattr(self, 'planing', None), 'name', None)
    
    @property
    def sub_project_name(self) -> str | None:
        return getattr(getattr(self, 'sub_project', None), 'name', None)
    
    @property
    def sub_project_code(self) -> str | None:
        return getattr(getattr(self, 'sub_project', None), 'code', None)
    
    @property
    def jumlah_bidang(self) -> int | None:
        jumlah = len(self.details)

        return jumlah or 0
    
    @property
    def dp_count(self) -> int | None:
        dp_termins = [dp for dp in self.termins if dp.jenis_bayar == JenisBayarEnum.DP]
        return len(dp_termins) or 0    
    
    @property
    def lunas_count(self) -> int | None:
        lunas_termins = [dp for dp in self.termins if dp.jenis_bayar == JenisBayarEnum.LUNAS]
        return len(lunas_termins) or 0    
    
    
class TahapDetailBase(SQLModel):
    tahap_id:UUID = Field(foreign_key="tahap.id", nullable=False)
    bidang_id:UUID = Field(foreign_key="bidang.id", nullable=False)
    is_void:Optional[bool] = Field(nullable=True)
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
    def alashak(self) -> str | None:
        return getattr(getattr(self, "bidang", None), "alashak", None)
    
    @property
    def group(self) -> str | None:
        return getattr(getattr(self, "bidang", None), "group", None)
    
    @property
    def alashak(self) -> str | None:
        return getattr(getattr(self, "bidang", None), "group", None)
    
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
    def harga_akta(self) -> Decimal | None:
        return getattr(getattr(self, "bidang", None), "harga_akta", None)
    
    @property
    def harga_transaksi(self) -> Decimal | None:
        return getattr(getattr(self, "bidang", None), "harga_transaksi", None)
    
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
    def planing_id(self) -> str | None:
        return getattr(getattr(self, "bidang", None), "planing_id", None)
    
    @property
    def ptsk_name(self) -> str | None:
        if self.bidang.skpt:
            return self.bidang.ptsk_name
        else:
            return (f'{self.bidang.penampung_name} (PENAMPUNG)')
    
    @property
    def ptsk_id(self) -> str | None:
        if self.bidang.skpt:
            return self.bidang.skpt.ptsk_id
        else:
            return self.bidang.penampung_id
    
    @property
    def total_harga_transaksi(self) -> Decimal | None:
        return self.bidang.total_harga_transaksi
    
    @property
    def total_harga_akta(self) -> Decimal | None:
        return self.bidang.total_harga_akta
    
    @property
    def sisa_pelunasan(self) -> Decimal | None:
        return self.bidang.sisa_pelunasan
    
    @property
    def overlaps(self) -> list[BidangOverlap] | None:
        return self.bidang.overlaps
        
    
