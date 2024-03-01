from models.spk_model import SpkBase, SpkFullBase
from common.partial import optional
from schemas.bidang_sch import BidangForSPKByIdSch
from schemas.spk_kelengkapan_dokumen_sch import SpkKelengkapanDokumenCreateExtSch, SpkKelengkapanDokumenSch, SpkKelengkapanDokumenUpdateExtSch
from schemas.bidang_komponen_biaya_sch import BidangKomponenBiayaExtSch, BidangKomponenBiayaSch
from common.enum import HasilAnalisaPetaLokasiEnum, JenisBayarEnum, SatuanBayarEnum, JenisBidangEnum, StatusSKEnum, TipeOverlapEnum
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
    created_name:str|None = Field(alias="created_name")
    updated_name:str|None = Field(alias="updated_name")
    group:str|None = Field(alias="group")

class SpkListSch(SpkSch):
    has_termin:bool|None = Field(alias="has_termin")
    nomor_memo:str|None = Field(alias="nomor_memo")
    has_on_tahap:bool|None = Field(alias="has_on_tahap")
    status_workflow:str|None
    step_name_workflow:str|None
    manager_name:str|None

class SpkHistorySch(SpkFullBase):
    id_bidang:str | None = Field(alias="id_bidang")
    alashak:str | None = Field(alias="alashak")
    nomor_memo:str|None = Field(alias="nomor_memo")

class SpkSrcSch(SQLModel):
    id:UUID|None
    code:str|None
    id_bidang:str|None
    amount:Decimal|None
    jenis_bayar:JenisBayarEnum|None
    alashak:str|None

class SpkByIdSch(SpkFullBase):
    bidang:BidangForSPKByIdSch | None
    created_name:str|None
    updated_name:str|None

    spk_beban_biayas:list[BidangKomponenBiayaSch] | None
    spk_kelengkapan_dokumens:list[SpkKelengkapanDokumenSch] | None

@optional
class SpkUpdateSch(SpkBase):
    spk_beban_biayas:list[BidangKomponenBiayaExtSch] | None
    spk_kelengkapan_dokumens:list[SpkKelengkapanDokumenUpdateExtSch] | None


class SpkPrintOut(SQLModel):
    bidang_id:Optional[UUID]
    kjb_hd_code:Optional[str]
    id_bidang:Optional[str]
    jenis_bidang:Optional[JenisBidangEnum]
    alashak:Optional[str]
    no_peta:Optional[str]
    group:Optional[str]
    luas_surat:Optional[Decimal]
    luas_ukur:Optional[Decimal]
    luas_gu_perorangan:Optional[Decimal] = Field(default=0)
    luas_pbt_perorangan:Optional[Decimal] = Field(default=0)
    pemilik_name:Optional[str]
    desa_name:Optional[str]
    project_name:Optional[str]
    ptsk_name:Optional[str]
    analisa:Optional[HasilAnalisaPetaLokasiEnum]
    jenis_bayar:Optional[JenisBayarEnum]
    amount:Optional[Decimal]
    satuan_bayar:Optional[SatuanBayarEnum]
    manager_name:Optional[str]
    sales_name:Optional[str]
    notaris_name:Optional[str]
    status_il:Optional[StatusSKEnum]
    worker_name:Optional[str]
    remark:Optional[str]

class SpkDetailPrintOut(SQLModel):
    bundle_dt_id:UUID|None
    no:Optional[int]
    tanggapan:Optional[str]
    name:Optional[str]

class SpkOverlapPrintOut(SQLModel):
    pemilik_name:Optional[str]
    alashak:Optional[str]
    tahap:Optional[str]
    luas_surat:Optional[Decimal]
    luas_overlap:Optional[Decimal]
    id_bidang:Optional[str]
    tipe_overlap:Optional[TipeOverlapEnum]

class SpkOverlapPrintOutExt(SpkOverlapPrintOut):
    luas_suratExt:Optional[str]
    luas_overlapExt:Optional[str]
    tipe_overlapExt:Optional[str]

class SpkRekeningPrintOut(SQLModel):
    rekening:Optional[str]

class SpkInTerminSch(SQLModel):
    spk_id:Optional[UUID]
    spk_code:Optional[str]
    spk_amount:Optional[Decimal]
    spk_satuan_bayar:Optional[str]
    jenis_bayar:Optional[JenisBayarEnum]
    bidang_id:Optional[UUID]
    id_bidang:Optional[str]
    alashak:Optional[str]
    group:Optional[str]
    project_id:Optional[UUID]
    project_name:Optional[str]
    sub_project_id:Optional[UUID]
    sub_project_name:Optional[str]
    nomor_tahap:Optional[int]
    tahap_id:Optional[UUID]
    luas_bayar:Optional[Decimal]
    harga_transaksi:Optional[Decimal]
    harga_akta:Optional[Decimal]
    amount:Optional[Decimal]
    utj_amount:Optional[Decimal]
    manager_id:Optional[UUID]
    manager_name:Optional[str]
    sales_id:Optional[UUID]
    sales_name:Optional[str]
    notaris_id:Optional[UUID]
    notaris_name:Optional[str]
    mediator:Optional[str]

class SpkVoidSch(SQLModel):
    void_reason:str


    

