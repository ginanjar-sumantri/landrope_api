from sqlmodel import SQLModel, Field, Relationship, select
from sqlalchemy import Column, String
from sqlalchemy.orm import column_property, declared_attr, aliased
from models.workflow_model import Workflow
from models.base_model import BaseUUIDModel, BaseHistoryModel
from common.enum import JenisBayarEnum, HasilAnalisaPetaLokasiEnum, SatuanBayarEnum
from uuid import UUID
from pydantic import condecimal
from typing import TYPE_CHECKING, Optional
from decimal import Decimal
from datetime import datetime, date

if TYPE_CHECKING:
    from models import Bidang, BundleDt, KjbTermin, Invoice, Worker

class SpkBase(SQLModel):
    code:Optional[str] = Field(nullable=True)
    bidang_id:UUID = Field(foreign_key="bidang.id", nullable=False)
    jenis_bayar:Optional[JenisBayarEnum] = Field(nullable=True)
    amount:Optional[condecimal(decimal_places=2)] = Field(nullable=True)
    satuan_bayar:SatuanBayarEnum | None = Field(nullable=True)
    kjb_termin_id:Optional[UUID] = Field(nullable=True, foreign_key="kjb_termin.id")
    remark:Optional[str] = Field(nullable=True)
    is_void:Optional[bool] = Field(nullable=True, default=False)
    void_by_id:Optional[UUID] = Field(foreign_key="worker.id", nullable=True)
    void_reason:Optional[str] = Field(nullable=True)
    void_at:Optional[date] = Field(nullable=True)
    file_path:str|None = Field(nullable=True)
    file_upload_path: str | None = Field(nullable = True)
    
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

    worker_updated: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "Spk.updated_by_id==Worker.id",
        }
    )

    worker_do_void: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "Spk.void_by_id==Worker.id",
        }
    )

    spk_histories: "SpkHistory" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        },
        back_populates="spk"
    )

    @property
    def id_bidang(self) -> str | None:
        return self.bidang.id_bidang
    
    @property
    def id_bidang_lama(self) -> str | None:
        return self.bidang.id_bidang_lama
    
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
    def manager_name(self) -> str | None:
        return getattr(getattr(self, "bidang", None), "manager_name", None)
    
    @property
    def created_name(self) -> str | None:
        return getattr(getattr(self, "worker", None), "name", None)
    
    @property
    def updated_name(self) -> str | None:
        return getattr(getattr(self, "worker_updated", None), "name", None)
    
    @property
    def has_invoice_active(self) -> bool | None:
        invoice = next((x for x in self.invoices if x.is_void != True), None)
        if invoice:
            return True
        
        return False
    
    @declared_attr
    def step_name_workflow(self) -> column_property:
        return column_property(
            select(
                Workflow.step_name
            )
            .select_from(
                Workflow)
            .where(Workflow.reference_id == self.id)
            .scalar_subquery()
        )
    
    @declared_attr
    def status_workflow(self) -> column_property:
        return column_property(
            select(
                Workflow.last_status
            )
            .select_from(
                Workflow)
            .where(Workflow.reference_id == self.id)
            .scalar_subquery()
        )

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
    

class SpkHistoryBase(SQLModel):
    spk_id:UUID = Field(foreign_key="spk.id", nullable=False)

class SpkHistoryBaseExt(SpkHistoryBase, BaseHistoryModel):
    pass

class SpkHistoryFullBase(BaseUUIDModel, SpkHistoryBaseExt):
    pass

class SpkHistory(SpkHistoryFullBase, table=True):
    spk:"Spk" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        },
        back_populates="spk_histories"
    )

    trans_worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "SpkHistory.trans_worker_id==Worker.id",
        }
    )

    @property
    def trans_worker_name(self) -> str | None:
        return getattr(getattr(self, "trans_worker", None), "name", None)