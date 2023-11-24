from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, String
from models.base_model import BaseUUIDModel
from common.enum import JenisBayarEnum, HasilAnalisaPetaLokasiEnum, SatuanBayarEnum
from uuid import UUID
from pydantic import condecimal
from typing import TYPE_CHECKING, Optional
from decimal import Decimal

if TYPE_CHECKING:
    from models import Bidang, BundleDt, KjbTermin, Invoice, Worker

class SpkBase(SQLModel):
    code:Optional[str] = Field(nullable=True)
    bidang_id:UUID = Field(foreign_key="bidang.id", nullable=False)
    jenis_bayar:Optional[JenisBayarEnum] = Field(nullable=True)
    amount:Optional[condecimal(decimal_places=2)] = Field(nullable=True)
    satuan_bayar:SatuanBayarEnum | None = Field(nullable=True)
    kjb_termin_id:Optional[UUID] = Field(nullable=True, foreign_key="kjb_termin.id")

class SpkFullBase(BaseUUIDModel, SpkBase):
    pass

class Spk(SpkFullBase, table=True):
    bidang:"Bidang" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select",

        }
    )

    invoices:list["Invoice"] = Relationship(
        back_populates="spk",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    spk_kelengkapan_dokumens:list["SpkKelengkapanDokumen"] = Relationship(
        back_populates="spk",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    kjb_termin:"KjbTermin" = Relationship(sa_relationship_kwargs=
        {
            "lazy" : "select",

        }
    )

    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "Spk.created_by_id==Worker.id",
        }
    )

    @property
    def id_bidang(self) -> str | None:
        return self.bidang.id_bidang
    
    @property
    def alashak(self) -> str | None:
        return self.bidang.alashak
    
    @property
    def group(self) -> str | None:
        return self.bidang.group
    
    @property
    def hasil_analisa_peta_lokasi(self) -> HasilAnalisaPetaLokasiEnum | None:
        return self.bidang.hasil_peta_lokasi.hasil_analisa_peta_lokasi
    
    @property
    def kjb_hd_code(self) -> str | None:
        return self.bidang.hasil_peta_lokasi.kjb_dt.kjb_code
    
    @property
    def spk_amount(self) -> Decimal | None:
        total_amount = self.amount
        if self.jenis_bayar == JenisBayarEnum.PENGEMBALIAN_BEBAN_PENJUAL:
            total_amount = self.bidang.total_pengembalian_beban_penjual
        elif self.jenis_bayar == JenisBayarEnum.BIAYA_LAIN:
            total_amount = self.bidang.biaya_lain_not_use
        else:
            if self.satuan_bayar == SatuanBayarEnum.Percentage:
                total_amount = ((self.amount or 0) * ((self.bidang.luas_bayar or 0) * (self.bidang.harga_transaksi or 0)))/100
            
        return Decimal(total_amount)
    
    @property
    def utj_amount(self) -> Decimal | None:
        utj = 0
        utj_is_used = any(invoice.use_utj == True for invoice in self.bidang.invoices if invoice.is_void != True)
        if utj_is_used == False:
            utj = self.bidang.utj_amount
            # utj_current = next((invoice_utj for invoice_utj in self.bidang.invoices 
            #                     if (invoice_utj.jenis_bayar == JenisBayarEnum.UTJ or invoice_utj.jenis_bayar == JenisBayarEnum.UTJ_KHUSUS) 
            #                     and invoice_utj.is_void != True))
            
            # if utj_current:
            #     amount_payment_details = [payment_detail.amount for payment_detail in utj_current.payment_details if payment_detail.is_void != True]
            #     utj = sum(amount_payment_details) or 0
        
        return Decimal(utj)
    
    @property
    def has_termin(self) -> bool | None:
        invoice = next((x for x in self.invoices if x.is_void != True), None)
        if invoice:
            return True
        
        return False
    
    @property
    def nomor_memo(self) -> str | None:
        invoice = next((x for x in self.invoices if x.is_void != True), None)
        if invoice:
            return invoice.nomor_memo
        
        return None
    
    @property
    def has_on_tahap(self) -> bool | None:
        tahap_detail = next((x for x in self.bidang.tahap_details if x.is_void != True), None)
        if tahap_detail:
            return True
        
        return False
    
    @property
    def created_name(self) -> str | None:
        return getattr(getattr(self, "worker", None), "name", None)
        
        


# class SpkBebanBiayaBase(SQLModel):
#     spk_id:UUID = Field(foreign_key="spk.id", nullable=False)
#     beban_biaya_id:UUID = Field(foreign_key="beban_biaya.id", nullable=False)
#     beban_pembeli:bool = Field(nullable=False)

# class SpkBebanBiayaFullBase(BaseUUIDModel, SpkBebanBiayaBase):
#     pass

# class SpkBebanBiaya(SpkBebanBiayaFullBase, table=True):
#     spk:"Spk" = Relationship(
#         back_populates="spk_beban_biayas",
#         sa_relationship_kwargs=
#         {
#             "lazy" : "selectin",
#             'foreign_keys': 'SpkBebanBiaya.spk_id'
#         }
#     )

#     beban_biaya:"BebanBiaya" = Relationship(
#         sa_relationship_kwargs=
#         {
#             "lazy" : "selectin"
#         }
#     )

#     @property
#     def beban_biaya_name(self) -> str :
#         if self.beban_biaya is None:
#             return ""
        
#         return self.beban_biaya.name


class SpkKelengkapanDokumenBase(SQLModel):
    spk_id:UUID = Field(foreign_key="spk.id", nullable=False)
    bundle_dt_id:UUID = Field(foreign_key="bundle_dt.id", nullable=False)
    tanggapan:str | None = Field(nullable=True)

class SpkKelengkapanDokumenFullBase(BaseUUIDModel, SpkKelengkapanDokumenBase):
    pass

class SpkKelengkapanDokumen(SpkKelengkapanDokumenFullBase, table=True):
    spk:"Spk" = Relationship(
        back_populates="spk_kelengkapan_dokumens",
        sa_relationship_kwargs=
        {
            "lazy" : "selectin",
            'foreign_keys': 'SpkKelengkapanDokumen.spk_id'
        }
    )

    bundledt:"BundleDt" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "selectin"
        }
    )

    @property
    def dokumen_name(self) -> str | None:
        return self.bundledt.dokumen_name or None
    
    @property
    def has_meta_data(self) -> bool | None:
        return self.bundledt.file_exists or False
    
    @property
    def file_path(self) -> bool | None:
        return getattr(getattr(self, "bundledt", None), "file_path", None)