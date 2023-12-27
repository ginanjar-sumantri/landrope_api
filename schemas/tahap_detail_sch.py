from models.tahap_model import TahapDetailBase, TahapDetailFullBase
from schemas.bidang_overlap_sch import BidangOverlapUpdateExtSch, BidangOverlapForTahap, BidangOverlapRawSch, BidangOverlapForPrintout
from sqlmodel import SQLModel, Field
from typing import Optional
from common.partial import optional
from common.as_form import as_form
from common.enum import HasilAnalisaPetaLokasiEnum, JenisBidangEnum
from uuid import UUID
from decimal import Decimal


class TahapDetailCreateSch(TahapDetailBase):
    pass

class TahapDetailCreateExtSch(SQLModel):
    bidang_id:Optional[UUID]
    harga_akta:Optional[Decimal]
    harga_transaksi:Optional[Decimal]
    luas_bayar:Optional[Decimal]
    overlaps:list[BidangOverlapUpdateExtSch] | None

class TahapDetailSch(TahapDetailFullBase):
    id_bidang:Optional[str] = Field(alias="id_bidang")
    alashak:Optional[str] = Field(alias="alashak")
    group:Optional[str] = Field(alias="group")
    luas_surat:Optional[Decimal] = Field(alias="luas_surat")
    luas_ukur:Optional[Decimal] = Field(alias="luas_ukur")
    luas_gu_perorangan:Optional[Decimal] = Field(alias="luas_gu_perorangan")
    luas_gu_pt:Optional[Decimal] = Field(alias="luas_gu_pt")
    luas_nett:Optional[Decimal] = Field(alias="luas_nett")
    luas_clear:Optional[Decimal] = Field(alias="luas_clear")
    luas_pbt_perorangan:Optional[Decimal] = Field(alias="luas_pbt_perorangan")
    luas_pbt_pt:Optional[Decimal] = Field(alias="luas_pbt_pt")
    luas_bayar:Optional[Decimal] = Field(alias="luas_bayar")
    harga_akta:Optional[Decimal] = Field(alias="harga_akta")
    harga_transaksi:Optional[Decimal] = Field(alias="harga_transaksi")
    project_name:Optional[str] = Field(alias="project_name")
    desa_name:Optional[str] = Field(alias="desa_name")
    planing_name:Optional[str] = Field(alias="planing_name")
    planing_id:Optional[UUID] = Field(alias="planing_id")
    ptsk_name:Optional[str] = Field(alias="ptsk_name")
    ptsk_id:Optional[UUID] = Field(alias="ptsk_id")
    pemiik_name:Optional[str] = Field(alias="pemilik_name")
    total_harga_transaksi:Optional[Decimal] = Field(alias="total_harga_transaksi")
    total_harga_akta:Optional[Decimal] = Field(alias="total_harga_akta")
    sisa_pelunasan:Optional[Decimal] = Field(alias="sisa_pelunasan")
    hasil_analisa_peta_lokasi:Optional[HasilAnalisaPetaLokasiEnum] = Field(alias="hasil_analisa_peta_lokasi")
    has_invoice:Optional[bool] = Field(alias="has_invoice")
    overlaps:Optional[list[BidangOverlapRawSch]] = Field(alias="overlaps")

class TahapDetailExtSch(SQLModel):
    id:UUID
    tahap_id:Optional[UUID]
    bidang_id:Optional[UUID]
    id_bidang:Optional[str]
    alashak:Optional[str]
    group:Optional[str]
    luas_surat:Optional[Decimal]
    luas_ukur:Optional[Decimal]
    luas_gu_perorangan:Optional[Decimal]
    luas_gu_pt:Optional[Decimal]
    luas_nett:Optional[Decimal] 
    luas_clear:Optional[Decimal] 
    luas_pbt_perorangan:Optional[Decimal] 
    luas_pbt_pt:Optional[Decimal] 
    luas_bayar:Optional[Decimal] 
    harga_akta:Optional[Decimal] 
    harga_transaksi:Optional[Decimal] 
    project_name:Optional[str] 
    desa_name:Optional[str] 
    planing_name:Optional[str]
    planing_id:Optional[UUID]
    ptsk_id:Optional[UUID]
    ptsk_name:Optional[str] 
    total_harga:Optional[Decimal]
    total_harga_akta:Optional[Decimal]
    total_beban:Optional[Decimal]
    total_invoice:Optional[Decimal]
    sisa_pelunasan:Optional[Decimal]
    overlaps:list[BidangOverlapForTahap] | None

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
    overlaps:list[BidangOverlapUpdateExtSch] | None

class TahapDetailForPrintOut(SQLModel):
    id:Optional[UUID]
    bidang_id:Optional[UUID]
    id_bidang:Optional[str]
    group:Optional[str]
    jenis_bidang:Optional[JenisBidangEnum]
    lokasi:Optional[str]
    ptsk_name:Optional[str]
    status_il:Optional[str]
    project_name:Optional[str]
    desa_name:Optional[str]
    pemilik_name:Optional[str]
    alashak:Optional[str]
    luas_surat:Optional[Decimal]
    luas_ukur:Optional[Decimal]
    luas_gu_perorangan:Optional[Decimal]
    luas_nett:Optional[Decimal]
    luas_pbt_perorangan:Optional[Decimal]
    luas_bayar:Optional[Decimal]
    no_peta:Optional[str]
    harga_transaksi:Optional[Decimal]
    total_harga:Optional[Decimal]

    no:Optional[int]
    harga_transaksiExt:Optional[str]
    total_hargaExt:Optional[str]
    luas_suratExt:Optional[str]
    luas_ukurExt:Optional[str]
    luas_gu_peroranganExt:Optional[str]
    luas_nettExt:Optional[str]
    luas_pbt_peroranganExt:Optional[str]
    luas_bayarExt:Optional[str]

    is_bold:Optional[bool]

    overlaps:Optional[list[BidangOverlapForPrintout]]
