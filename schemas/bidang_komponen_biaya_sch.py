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
    beban_biaya_id:UUID | None
    beban_pembeli:bool | None
    is_void:Optional[bool]
    remark:Optional[str]


class BidangKomponenBiayaSch(BidangKomponenBiayaFullBase):
    updated_by_name:str|None = Field(alias="updated_by_name")
    beban_biaya_name:Optional[str] = Field(alias="beban_biaya_name")

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
    name:Optional[str]
    satuan_harga:Optional[SatuanHargaEnum]
    satuan_bayar:Optional[SatuanBayarEnum]
    beban_biaya_amount:Optional[Decimal]
    total_beban:Optional[Decimal]
