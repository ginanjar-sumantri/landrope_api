from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from common.enum import TanggunganBiayaEnum, SatuanBayarEnum, SatuanHargaEnum
from uuid import UUID
from datetime import date
from typing import TYPE_CHECKING, Optional
from pydantic import condecimal
from decimal import Decimal

if TYPE_CHECKING:
    from bidang_model import Bidang
    from master_model import BebanBiaya
    from worker_model import Worker

class BidangKomponenBiayaBase(SQLModel):
    bidang_id:UUID = Field(foreign_key="bidang.id", nullable=False)
    beban_biaya_id:UUID = Field(foreign_key="beban_biaya.id", nullable=False)
    beban_pembeli:Optional[bool] = Field(nullable=True)
    is_use:Optional[bool] = Field(nullable=True)
    tanggal_bayar:Optional[date] = Field(nullable=True)
    is_paid:Optional[bool] = Field(nullable=True)
    is_void:Optional[bool] = Field(nullable=True)
    remark:Optional[str] = Field(nullable=True)
    satuan_bayar:Optional[SatuanBayarEnum] = Field(nullable=True)
    satuan_harga:Optional[SatuanHargaEnum] = Field(nullable=True)
    amount:Optional[condecimal(decimal_places=2)] = Field(nullable=True)
    # amount_calculate:Optional[Decimal] = Field(nullable=True)
    
    
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
    def beban_biaya_name(self) -> str :
        return getattr(getattr(self, 'beban_biaya', None), 'name', None)
    
    @property
    def is_tax(self) -> bool | None :
        return getattr(getattr(self, 'beban_biaya', None), 'is_tax', None)
    
    @property
    def amount_calculate(self) -> Decimal | None:
        total_amount:Decimal = 0
        if self.satuan_bayar == SatuanBayarEnum.Percentage and self.satuan_harga == SatuanHargaEnum.PerMeter2:
            total_amount = (self.amount or 0) * ((self.bidang.luas_bayar or self.bidang.luas_surat) * (self.bidang.harga_transaksi or 0)/100)
        elif self.satuan_bayar == SatuanBayarEnum.Amount and self.satuan_harga == SatuanHargaEnum.PerMeter2:
            total_amount = (self.amount or 0) * (self.bidang.luas_bayar or self.bidang.luas_surat)
        else:
            total_amount = (self.amount or 0)
        
        return total_amount


