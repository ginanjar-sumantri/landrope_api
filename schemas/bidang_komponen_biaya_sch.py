from models.bidang_komponen_biaya_model import BidangKomponenBiaya, BidangKomponenBiayaBase, BidangKomponenBiayaFullBase
from common.partial import optional
from common.as_form import as_form
from common.enum import SatuanBayarEnum, SatuanHargaEnum
from sqlmodel import SQLModel, Field
from uuid import UUID
from typing import Optional
from decimal import Decimal

class BidangKomponenBiayaCreateSch(BidangKomponenBiayaBase):
    pass

class BidangKomponenBiayaExtSch(SQLModel):
    id:UUID | None
    beban_biaya_id:UUID | None
    beban_pembeli:bool | None
    is_void:Optional[bool]
    remark:Optional[str]
    satuan_bayar:Optional[SatuanBayarEnum]
    satuan_harga:Optional[SatuanHargaEnum]
    amount:Optional[Decimal]
    order_number:int | None


class BidangKomponenBiayaSch(BidangKomponenBiayaFullBase):
    updated_by_name:str|None = Field(alias="updated_by_name")
    beban_biaya_name:Optional[str] = Field(alias="beban_biaya_name")
    is_edit:Optional[bool] = Field(alias="is_edit")
    is_tax:Optional[bool] = Field(alias="is_tax")
    komponen_biaya_outstanding:Optional[Decimal] = Field(alias="komponen_biaya_outstanding")
    invoice_detail_amount:Optional[Decimal] = Field(alias="invoice_detail_amount")
    is_exclude_printout:bool | None

    

class BidangKomponenBiayaListSch(BidangKomponenBiayaSch):
    amount_calculate:Decimal|None = Field(alias="amount_calculate")
    has_invoice_lunas:bool|None = Field(alias="has_invoice_lunas")

@optional
class BidangKomponenBiayaUpdateSch(BidangKomponenBiayaBase):
    pass

class BidangKomponenBiayaBebanPenjualSch(SQLModel):
    bidang_id:Optional[UUID]
    id_bidang:Optional[str]
    alashak:Optional[str]
    luas_surat:Optional[Decimal]
    luas_bayar:Optional[Decimal]
    harga_transaksi:Optional[Decimal]
    komponen_id:Optional[UUID]
    beban_pembeli:Optional[bool]
    name:Optional[str]
    satuan_harga:Optional[SatuanHargaEnum]
    satuan_bayar:Optional[SatuanBayarEnum]
    beban_biaya_amount:Optional[Decimal]
    total_beban:Optional[Decimal]
    is_void:Optional[bool]
    is_retur:Optional[bool]
    is_add_pay:Optional[bool]
    estimasi_amount:Optional[Decimal]
    paid_amount:Optional[Decimal]


