from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from common.enum import TipeSuratGambarUkurEnum, JenisAlashakEnum, HasilAnalisaPetaLokasiEnum, ProsesBPNOrderGambarUkurEnum
from uuid import UUID
from typing import TYPE_CHECKING
from decimal import Decimal

if TYPE_CHECKING:
    from models.worker_model import Worker
    from models.notaris_model import Notaris
    from models.kjb_model import KjbDt

class OrderGambarUkurBase(SQLModel):
    code:str | None = Field(nullable=True)
    status_bidang:HasilAnalisaPetaLokasiEnum | None = Field(nullable=True)
    tipe_surat:TipeSuratGambarUkurEnum
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
            "lazy" : "select"
        }
    )

    bidangs:list["OrderGambarUkurBidang"] = Relationship(
        back_populates="order_gambar_ukur",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    tembusans:list["OrderGambarUkurTembusan"] = Relationship(
        back_populates="order_gambar_ukur",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
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
    
    @property
    def perihal(self) -> str | None:
        if self.status_bidang == HasilAnalisaPetaLokasiEnum.Clear:
            if len(self.bidangs) > 0:
                bidang = self.bidangs[0]
                if bidang.kjb_dt.hasil_peta_lokasi is None:
                    return None
                
                pbt = bidang.proses_bpn_order_gu
                if pbt == ProsesBPNOrderGambarUkurEnum.PBT_Perorangan:
                    return "Proses Gambar Ukur Perorangan (Bidang Clear)"
                elif pbt == ProsesBPNOrderGambarUkurEnum.PBT_PT:
                    return "Proses Gambar Ukur PT (Bidang Clear)"
                else:
                    return None
            else:
                return None
        if self.status_bidang == HasilAnalisaPetaLokasiEnum.Overlap:
            if len(self.bidangs) > 0:
                bidang = self.bidangs[0]
                if bidang.kjb_dt.hasil_peta_lokasi is None:
                    return None
                
                pbt = bidang.proses_bpn_order_gu
                if pbt == ProsesBPNOrderGambarUkurEnum.PBT_Perorangan:
                    return "Proses Gambar Ukur Perorangan (Bidang Overlap)"
                elif pbt == ProsesBPNOrderGambarUkurEnum.PBT_PT:
                    return "Proses Gambar Ukur PT (Bidang Overlap)"
                else:
                    return None
            else:
                return None
    
    

class OrderGambarUkurBidangBase(SQLModel):
    order_gambar_ukur_id:UUID | None = Field(nullable=False, foreign_key="order_gambar_ukur.id")
    kjb_dt_id:UUID = Field(nullable=False, foreign_key="kjb_dt.id")

class OrderGambarUkurBidangFullBase(BaseUUIDModel, OrderGambarUkurBidangBase):
    pass

class OrderGambarUkurBidang(OrderGambarUkurBidangFullBase, table=True):
    order_gambar_ukur:"OrderGambarUkur" = Relationship(
        back_populates="bidangs",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    kjb_dt:"KjbDt" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    @property
    def id_bidang(self) -> str | None:
        return getattr(getattr(getattr(getattr(self, "kjb_dt", None), "hasil_peta_lokasi", None), "bidang", None), "id_bidang", None)
    
    @property
    def jenis_alashak(self) -> JenisAlashakEnum | None:
        return getattr(getattr(self, "kjb_dt", None), "jenis_alashak", None)
    
    @property
    def alashak(self) -> str | None:
        return getattr(getattr(self, "kjb_dt", None), "alashak", None)
    
    @property
    def hasil_analisa_peta_lokasi(self) -> HasilAnalisaPetaLokasiEnum | None:
        return getattr(getattr(getattr(getattr(self, "kjb_dt", None), "hasil_peta_lokasi", None), "bidang", None), "hasil_analisa_peta_lokasi", None)
    
    @property
    def proses_bpn_order_gu(self) -> ProsesBPNOrderGambarUkurEnum | None:
        if self.kjb_dt.hasil_peta_lokasi is None:
            return None
        elif self.kjb_dt.hasil_peta_lokasi.bidang is None:
            return None
        else:
            return self.kjb_dt.hasil_peta_lokasi.bidang.proses_bpn_order_gu
    
    @property
    def pemilik_name(self) -> str | None:
        if self.kjb_dt.hasil_peta_lokasi is None:
            return getattr(getattr(getattr(self, "kjb_dt", None), "pemilik", None), "name", None)
        else:
            if self.kjb_dt.hasil_peta_lokasi.bidang is None:
                return getattr(getattr(getattr(self, "kjb_dt", None), "pemilik", None), "name", None)
            else:
                return getattr(getattr(getattr(getattr(self, "kjb_dt", None), "hasil_peta_lokasi", None), "bidang", None), "pemilik_name", None)
        
    @property
    def group(self) -> str | None:
        if self.kjb_dt.hasil_peta_lokasi is None:
            return getattr(getattr(getattr(self, "kjb_dt", None), "kjb_hd", None), "nama_group", None)
        else:
            if self.kjb_dt.hasil_peta_lokasi.bidang is None:
                return getattr(getattr(getattr(self, "kjb_dt", None), "kjb_hd", None), "nama_group", None)
            else:
                return getattr(getattr(getattr(getattr(self, "kjb_dt", None), "hasil_peta_lokasi", None), "bidang", None), "group", None)
    
    @property
    def ptsk_name(self) -> str | None:
        return getattr(getattr(getattr(getattr(self, "kjb_dt", None), "hasil_peta_lokasi", None), "bidang", None), "ptsk_name", None)
    
    @property
    def jenis_surat_name(self) -> str | None:
        if self.kjb_dt.hasil_peta_lokasi is None:
            return getattr(getattr(self, "kjb_dt", None), "jenis_surat_name", None)
        else:
            if self.kjb_dt.hasil_peta_lokasi.bidang is None:
                return getattr(getattr(self, "kjb_dt", None), "jenis_surat_name", None)
            else:
                return getattr(getattr(getattr(getattr(self, "kjb_dt", None), "hasil_peta_lokasi", None), "bidang", None), "jenis_surat_name", None)
    
    @property
    def luas_surat(self) -> Decimal | None:
        if self.kjb_dt.hasil_peta_lokasi is None:
            return getattr(getattr(self, "kjb_dt", None), "luas_surat_by_ttn", None)
        else:
            if self.kjb_dt.hasil_peta_lokasi.bidang is None:
                return getattr(getattr(self, "kjb_dt", None), "luas_surat_by_ttn", None)
            else:
                return getattr(getattr(getattr(getattr(self, "kjb_dt", None), "hasil_peta_lokasi", None), "bidang", None), "luas_surat", None)
    
    @property
    def mediator(self) -> str | None:
        return getattr(getattr(getattr(self, "kjb_dt", None), "kjb_hd", None), "mediator", None)
    
    @property
    def sales_name(self) -> str | None:
        return getattr(getattr(getattr(self, "kjb_dt", None), "kjb_hd", None), "sales_name", None)
    
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
            "lazy" : "select"
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