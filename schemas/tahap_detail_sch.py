from models.tahap_model import TahapDetailBase, TahapDetailFullBase
from sqlmodel import SQLModel, Field
from typing import Optional
from common.partial import optional
from common.as_form import as_form
from uuid import UUID
from decimal import Decimal


class TahapDetailCreateSch(TahapDetailBase):
    pass

class TahapDetailCreateExtSch(SQLModel):
    bidang_id:Optional[UUID]
    harga_akta:Optional[Decimal]
    harga_transaksi:Optional[Decimal]
    luas_bayar:Optional[Decimal]

class TahapDetailSch(TahapDetailFullBase):
    id_bidang:Optional[str] = Field(alias="id_bidang")
    luas_surat:Optional[Decimal] = Field(alias="luas_surat")
    luas_ukur:Optional[Decimal] = Field(alias="luas_ukur")
    luas_gu_perorangan:Optional[Decimal] = Field(alias="luas_gu_perorangan")
    luas_gu_pt:Optional[Decimal] = Field(alias="luas_gu_pt")
    luas_nett:Optional[Decimal] = Field(alias="luas_nett")
    luas_clear:Optional[Decimal] = Field(alias="luas_clear")
    luas_pbt_perorangan:Optional[Decimal] = Field(alias="luas_pbt_perorangan")
    luas_pbt_pt:Optional[Decimal] = Field(alias="luas_pbt_pt")
    luas_bayar:Optional[Decimal] = Field(alias="luas_bayar")
    satuan:Optional[Decimal] = Field(alias="satuan")
    satuan_akta:Optional[Decimal] = Field(alias="satuan_akta")
    project_name:Optional[str] = Field(alias="project_name")
    desa_name:Optional[str] = Field(alias="desa_name")
    planing_name:Optional[str] = Field(alias="planing_name")
    ptsk_name:Optional[str] = Field(alias="ptsk_name")
    harga_total:Optional[Decimal] = Field(alias="harga_total")
    sisa_pelunasan:Optional[Decimal]

@optional
class TahapDetailUpdateSch(TahapDetailBase):
    pass

class TahapDetailUpdateExtSch(SQLModel):
    id:Optional[UUID]
    bidang_id:UUID
    harga_akta:Optional[Decimal]
    harga_transaksi:Optional[Decimal]
    luas_bayar:Optional[Decimal]
    is_void:Optional[bool] = Field(default=False)
