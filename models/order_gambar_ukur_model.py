from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from common.enum import TipeSuratGambarUkurEnum, JenisAlashakEnum, HasilAnalisaPetaLokasiEnum, ProsesBPNOrderGambarUkurEnum
from uuid import UUID
from typing import TYPE_CHECKING
from decimal import Decimal

if TYPE_CHECKING:
    from models.worker_model import Worker
    from models.notaris_model import Notaris
    from models.bidang_model import Bidang

class OrderGambarUkurBase(SQLModel):
    tipe_surat:TipeSuratGambarUkurEnum
    code:str
    tujuan_surat_worker_id:UUID | None = Field(nullable=True, foreign_key="worker.id")
    tujuan_surat_notaris_id:UUID | None = Field(nullable=True, foreign_key="notaris.id")

class OrderGambarUkurFullBase(BaseUUIDModel, OrderGambarUkurBase):
    pass

class OrderGambarUkur(OrderGambarUkurFullBase, table=True):
    worker:"Worker" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "joined",
            "primaryjoin" : "OrderGambarUkur.created_by_id == Worker.id"
        }
    )
    worker_tujuan:"Worker" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "joined",
            "primaryjoin" : "OrderGambarUkur.tujuan_surat_worker_id == Worker.id"
        }
    )

    notaris_tujuan:"Notaris" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "selectin"
        }
    )

    bidangs:list["OrderGambarUkurBidang"] = Relationship(
        back_populates="order_gambar_ukur",
        sa_relationship_kwargs=
        {
            "lazy" : "selectin"
        }
    )

    tembusans:list["OrderGambarUkurTembusan"] = Relationship(
        back_populates="order_gambar_ukur",
        sa_relationship_kwargs=
        {
            "lazy" : "selectin"
        }
    )

    @property
    def tujuan_surat(self) -> str | None:
        if self.notaris_tujuan:
            return self.notaris_tujuan.name
        if self.worker_tujuan:
            return self.worker_tujuan.name
        
        return None
    
    @property
    def created_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)
    

class OrderGambarUkurBidangBase(SQLModel):
    order_gambar_ukur_id:UUID | None = Field(nullable=False, foreign_key="order_gambar_ukur.id")
    bidang_id:UUID = Field(nullable=False, foreign_key="bidang.id")

class OrderGambarUkurBidangFullBase(BaseUUIDModel, OrderGambarUkurBidangBase):
    pass

class OrderGambarUkurBidang(OrderGambarUkurBidangFullBase, table=True):
    order_gambar_ukur:"OrderGambarUkur" = Relationship(
        back_populates="bidangs",
        sa_relationship_kwargs=
        {
            "lazy" : "selectin"
        }
    )

    bidang:"Bidang" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "selectin"
        }
    )

    @property
    def id_bidang(self) -> str | None:
        return getattr(getattr(self, "bidang", None), "id_bidang", None)
    
    @property
    def jenis_alashak(self) -> JenisAlashakEnum | None:
        return getattr(getattr(self, "bidang", None), "jenis_alashak", None)
    
    @property
    def alashak(self) -> str | None:
        return getattr(getattr(self, "bidang", None), "alashak", None)
    
    @property
    def hasil_analisa_peta_lokasi(self) -> HasilAnalisaPetaLokasiEnum | None:
        return getattr(getattr(self, "bidang", None), "hasil_analisa_peta_lokasi", None)
    
    @property
    def proses_bpn_order_gu(self) -> ProsesBPNOrderGambarUkurEnum | None:
        return getattr(getattr(self, "bidang", None), "proses_bpn_order_gu", None)
    
    @property
    def pemilik_name(self) -> str | None:
        return getattr(getattr(getattr(self, "bidang", None), "pemilik", None), "name", None)
    
    @property
    def group(self) -> str | None:
        return getattr(getattr(self, "bidang", None), "group", None)
    
    @property
    def ptsk_name(self) -> str | None:
        return getattr(getattr(getattr(getattr(self, "bidang", None), "skpt", None), "ptsk", None), "name", None)
    
    @property
    def jenis_surat_name(self) -> str | None:
        return getattr(getattr(getattr(self, "bidang", None), "pemilik", None), "name", None)
    
    @property
    def luas_surat(self) -> Decimal | None:
        return getattr(getattr(self, "bidang", None), "luas_surat", None)

    

    
class OrderGambarUkurTembusanBase(SQLModel):
    order_gambar_ukur_id:UUID | None = Field(nullable=False, foreign_key="order_gambar_ukur.id")
    tembusan_id:UUID = Field(nullable=False, foreign_key="worker.id")

class OrderGambarUkurTembusanFullBase(BaseUUIDModel, OrderGambarUkurTembusanBase):
    pass

class OrderGambarUkurTembusan(OrderGambarUkurTembusanFullBase, table=True):
    order_gambar_ukur:"OrderGambarUkur" = Relationship(
        back_populates="tembusans",
        sa_relationship_kwargs=
        {
            "lazy" : "selectin"
        }
    )

    tembusan:"Worker" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "joined",
            "primaryjoin" : "OrderGambarUkurTembusan.tembusan_id == Worker.id"
        }
    )

    @property
    def cc_name(self) -> str | None:
        return getattr(getattr(self, "tembusan", None), "name", None)