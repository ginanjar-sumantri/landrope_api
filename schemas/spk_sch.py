from models.spk_model import SpkBase, SpkFullBase
from common.partial import optional
from schemas.bidang_sch import BidangForSPKByIdSch
from schemas.spk_kelengkapan_dokumen_sch import SpkKelengkapanDokumenCreateExtSch, SpkKelengkapanDokumenSch, SpkKelengkapanDokumenUpdateExtSch
from schemas.bidang_komponen_biaya_sch import BidangKomponenBiayaExtSch, BidangKomponenBiayaSch
from common.enum import HasilAnalisaPetaLokasiEnum, JenisBayarEnum, SatuanBayarEnum
from sqlmodel import Field, SQLModel
from typing import Optional
from decimal import Decimal
from uuid import UUID


class SpkCreateSch(SpkBase):
    spk_beban_biayas:list[BidangKomponenBiayaExtSch] | None
    spk_kelengkapan_dokumens:list[SpkKelengkapanDokumenCreateExtSch] | None

class SpkSch(SpkFullBase):
    id_bidang:str | None = Field(alias="id_bidang")
    alashak:str | None = Field(alias="alashak")
    hasil_analisa_peta_lokasi:HasilAnalisaPetaLokasiEnum | None = Field(alias="hasil_analisa_peta_lokasi")
    kjb_hd_code:str | None = Field(alias="kjb_hd_code")

class SpkSrcSch(SQLModel):
    id:UUID
    code:str
    id_bidang:str

class SpkByIdSch(SpkFullBase):
    bidang:BidangForSPKByIdSch | None

    spk_beban_biayas:list[BidangKomponenBiayaSch] | None
    spk_kelengkapan_dokumens:list[SpkKelengkapanDokumenSch] | None

@optional
class SpkUpdateSch(SpkBase):
    spk_beban_biayas:list[BidangKomponenBiayaExtSch] | None
    spk_kelengkapan_dokumens:list[SpkKelengkapanDokumenUpdateExtSch] | None


class SpkPrintOut(SQLModel):
    kjb_hd_code:Optional[str]
    id_bidang:Optional[str]
    alashak:Optional[str]
    no_peta:Optional[str]
    group:Optional[str]
    luas_surat:Optional[Decimal]
    luas_ukur:Optional[Decimal]
    pemilik_name:Optional[str]
    desa_name:Optional[str]
    project_name:Optional[str]
    ptsk_name:Optional[str]
    analisa:Optional[HasilAnalisaPetaLokasiEnum]
    jenis_bayar:Optional[JenisBayarEnum]
    nilai:Optional[Decimal]
    satuan_bayar:Optional[SatuanBayarEnum]
    manager_name:Optional[str]
    sales_name:Optional[str]

class SpkForTerminSch(SQLModel):
    spk_id:Optional[UUID]
    spk_code:Optional[str]
    spk_amount:Optional[Decimal]
    spk_nilai:Optional[Decimal]
    spk_satuan_bayar:Optional[str]
    bidang_id:Optional[UUID]
    id_bidang:Optional[str]
    alashak:Optional[str]
    group:Optional[str]
    luas_bayar:Optional[Decimal]
    harga_transaksi:Optional[Decimal]
    harga_akta:Optional[Decimal]
    total_harga:Optional[Decimal]
    total_beban:Optional[Decimal]
    total_invoice:Optional[Decimal]
    sisa_pelunasan:Optional[Decimal]
    amount:Optional[Decimal]
    

