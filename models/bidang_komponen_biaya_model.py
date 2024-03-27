from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from common.enum import JenisBayarEnum, SatuanBayarEnum, SatuanHargaEnum
from uuid import UUID
from datetime import date
from typing import TYPE_CHECKING, Optional
from pydantic import condecimal
from decimal import Decimal

if TYPE_CHECKING:
    from models import Bidang, BebanBiaya, Worker, InvoiceDetail

class BidangKomponenBiayaBase(SQLModel):
    bidang_id:UUID = Field(foreign_key="bidang.id", nullable=False)
    beban_biaya_id:UUID = Field(foreign_key="beban_biaya.id", nullable=False)
    beban_pembeli:Optional[bool] = Field(nullable=True)
    tanggal_bayar:Optional[date] = Field(nullable=True)
    is_paid:Optional[bool] = Field(nullable=True)
    is_void:Optional[bool] = Field(nullable=True)
    is_add_pay:Optional[bool] = Field(nullable=True)
    is_retur:Optional[bool] = Field(nullable=True)
    remark:Optional[str] = Field(nullable=True)
    satuan_bayar:Optional[SatuanBayarEnum] = Field(nullable=True)
    satuan_harga:Optional[SatuanHargaEnum] = Field(nullable=True)
    amount:Optional[Decimal] = Field(nullable=True)
    paid_amount:Optional[Decimal] = Field(nullable=True)
    estimated_amount:Optional[Decimal] = Field(nullable=True)
    formula:Optional[str] = Field(nullable=True)
    order_number:int | None = Field(nullable=True)
    is_exclude_spk:bool | None = Field(nullable=True)
    
class BidangKomponenBiayaFullBase(BaseUUIDModel, BidangKomponenBiayaBase):
    pass

class BidangKomponenBiaya(BidangKomponenBiayaFullBase, table=True):
    bidang:"Bidang" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "selectin"
        }
    )

    beban_biaya:"BebanBiaya" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "selectin"
        }
    )

    invoice_details:list["InvoiceDetail"] = Relationship(
        back_populates="bidang_komponen_biaya",
        sa_relationship_kwargs=
        {
            "lazy" : "selectin"
        }
    )

    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "BidangKomponenBiaya.updated_by_id==Worker.id",
        }
    )

    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)
    
    @property
    def beban_biaya_name(self) -> str | None:
        return getattr(getattr(self, 'beban_biaya', None), 'name', None)
    
    @property
    def is_tax(self) -> bool | None :
        return getattr(getattr(self, 'beban_biaya', None), 'is_tax', None)
    
    @property
    def is_edit(self) -> bool | None :
        return getattr(getattr(self, 'beban_biaya', False), 'is_edit', False)
    
    @property
    def is_exclude_printout(self) -> bool | None :
        return getattr(getattr(self, 'beban_biaya', None), 'is_exclude_printout', None)
    
    @property
    def komponen_biaya_outstanding(self) -> Decimal | None:
        outstanding:Decimal = 0
        if self.is_retur:
            outstanding = self.invoice_detail_amount
        else:
            outstanding = (self.estimated_amount or 0) - self.invoice_detail_amount
        
        return outstanding
    
    @property
    def invoice_detail_amount(self) -> Decimal | None:
        amount:Decimal = 0
        if self.is_void != True:
            invoice_detail_amounts = [(inv_dtl.amount or 0) for inv_dtl in self.invoice_details if inv_dtl.invoice.is_void != True]
            amount = sum(invoice_detail_amounts)
       
        return amount
    
    @property
    def amount_biaya_lain(self) -> Decimal | None:
        if self.is_add_pay and self.is_void != True and self.beban_pembeli:
            return self.amount or 0
        
        return 0
    
    @property
    def has_invoice_lunas(self) -> bool | None:
        return getattr(getattr(self, "bidang", False), "has_invoice_lunas", False)
    
    #region NOT USE
    # @property
    # def amount_calculate(self) -> Decimal | None:
    #     total_amount:Decimal = 0
    #     if self.beban_biaya.is_njop:
    #         harga_akta = self.bidang.harga_akta * self.bidang.luas_surat
    #         harga_njop = self.bidang.njop * self.bidang.luas_surat

    #         harga_terbesar = max(harga_akta, harga_njop)

    #         total_amount = (self.amount * harga_terbesar)/100
    #     else:
    #         if self.satuan_bayar == SatuanBayarEnum.Percentage and self.satuan_harga == SatuanHargaEnum.PerMeter2:
    #             total_amount = (self.amount or 0) * ((self.bidang.luas_bayar or self.bidang.luas_surat) * (self.bidang.harga_transaksi or 0)/100)
    #         elif self.satuan_bayar == SatuanBayarEnum.Amount and self.satuan_harga == SatuanHargaEnum.PerMeter2:
    #             total_amount = (self.amount or 0) * (self.bidang.luas_bayar or self.bidang.luas_surat)
    #         else:
    #             total_amount = (self.amount or 0)
        
    #     return total_amount
    #endregion

    


