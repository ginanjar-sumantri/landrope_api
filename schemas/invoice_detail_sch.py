from models.invoice_model import InvoiceDetail, InvoiceDetailBase, InvoiceDetailFullBase
from common.partial import optional
from common.enum import SatuanBayarEnum, SatuanHargaEnum
from sqlmodel import SQLModel, Field
from typing import Optional
from uuid import UUID
from decimal import Decimal

class InvoiceDetailCreateSch(InvoiceDetailBase):
    pass

class InvoiceDetailExtSch(SQLModel):
    id:Optional[UUID]
    bidang_komponen_biaya_id:Optional[UUID]
    beban_biaya_id:UUID | None
    is_exclude_spk:bool | None
    amount:Optional[Decimal]
    is_deleted:bool | None
    beban_pembeli:bool | None
    satuan_bayar: SatuanBayarEnum | None
    satuan_harga: SatuanHargaEnum | None
    komponen_biaya_amount: Decimal | None

class InvoiceDetailSch(InvoiceDetailFullBase):
    updated_by_name:str|None = Field(alias="updated_by_name")
    amount:Decimal|None = Field(alias="amount")
    is_void:bool|None = Field(alias="is_void")
    beban_biaya_name:str|None = Field(alias="beban_biaya_name")
    beban_biaya_id: UUID | None
    satuan_bayar: SatuanBayarEnum | None
    satuan_harga: SatuanHargaEnum | None
    komponen_biaya_amount: Decimal | None
    is_retur: bool | None

@optional
class InvoiceDetailUpdateSch(InvoiceDetailBase):
    pass