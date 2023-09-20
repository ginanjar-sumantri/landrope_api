from models.bidang_model import BidangBase, BidangRawBase, BidangFullBase
from models.base_model import BaseGeoModel
from schemas.kjb_termin_sch import KjbTerminSch
from schemas.kjb_beban_biaya_sch import KjbBebanBiayaSch
from schemas.checklist_kelengkapan_dokumen_dt_sch import ChecklistKelengkapanDokumenDtSch
from common.partial import optional
from common.as_form import as_form
from common.enum import JenisAlashakEnum, StatusSKEnum, HasilAnalisaPetaLokasiEnum, ProsesBPNOrderGambarUkurEnum, SatuanBayarEnum
from sqlmodel import Field, SQLModel
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from uuid import UUID

@as_form
class BidangCreateSch(BidangBase):
    pass

class BidangRawSch(BidangRawBase):
    pemilik_name:str|None = Field(alias='pemilik_name')
    project_name:str|None = Field(alias='project_name')
    desa_name:str|None = Field(alias='desa_name')
    updated_by_name:str|None = Field(alias='updated_by_name')

class BidangByIdSch(BidangRawBase):
    pemilik_name:str|None = Field(alias='pemilik_name')
    project_name:str|None = Field(alias='project_name')
    desa_name:str|None = Field(alias='desa_name')
    planing_name:str|None = Field(alias='planing_name')
    jenis_surat_name:str|None = Field(alias='jenis_surat_name')
    kategori_name:str|None = Field(alias='kategori_name')
    kategori_sub_name:str|None = Field(alias='kategori_sub_name')
    kategori_proyek_name:str|None = Field(alias='kategori_proyek_name')
    ptsk_name:str | None = Field(alias='ptsk_name')
    no_sk:str|None = Field(alias='no_sk')
    status_sk:str|None = Field(alias='status_sk')
    penampung_name:str|None = Field(alias='penampung_name')
    manager_name:str | None = Field(alias='manager_name')
    sales_name:str|None = Field(alias='sales_name')
    notaris_name:str | None = Field(alias='notaris_name')

@as_form
@optional
class BidangUpdateSch(BidangBase):
    pass


class BidangForOrderGUById(SQLModel):
    id:UUID | None
    id_bidang:str | None
    jenis_alashak:JenisAlashakEnum | None
    alashak:str | None
    status_sk:StatusSKEnum | None
    ptsk_name:str | None
    hasil_analisa_peta_lokasi:HasilAnalisaPetaLokasiEnum | None
    proses_bpn_order_gu:ProsesBPNOrderGambarUkurEnum | None
    luas_surat:Decimal | None

class BidangForSPKByIdSch(SQLModel):
    id:UUID | None
    id_bidang:str | None
    hasil_analisa_peta_lokasi:HasilAnalisaPetaLokasiEnum | None
    kjb_no:str | None
    satuan_bayar:SatuanBayarEnum | None
    group:str | None
    pemilik_name:str | None
    alashak:str | None
    desa_name:str | None
    project_name:str | None
    luas_surat:Decimal | None
    luas_ukur:Decimal | None
    no_peta:str | None
    notaris_name:str | None
    ptsk_name:str | None
    status_sk:str | None
    bundle_hd_id:UUID | None

    termins:list[KjbTerminSch] | None

class BidangForSPKByIdExtSch(BidangForSPKByIdSch):
    beban_biayas:list[KjbBebanBiayaSch] | None
    kelengkapan_dokumens:list[ChecklistKelengkapanDokumenDtSch] | None

class BidangForTahapByIdSch(SQLModel):
    id:Optional[UUID]
    id_bidang:Optional[str]
    project_name:Optional[str]
    desa_name:Optional[str]
    planing_name:Optional[str]
    planing_id:Optional[UUID]
    ptsk_name:Optional[str]
    ptsk_id:Optional[UUID]
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
    alashak:Optional[str]
    no_peta:Optional[str]
    group:Optional[str]

class BidangDraftChecklistDokumenSch(SQLModel):
    bundle_dt_id:UUID | None
    jenis_bayar:str | None
    dokumen_id:UUID | None
    
class BidangSch(BidangFullBase):
    pass

class BidangShpSch(BaseGeoModel):
    n_idbidang:str | None
    o_idbidang:str | None
    pemilik:str | None
    code_desa:str | None
    dokumen:str | None
    sub_surat:str | None
    alashak:str | None
    luassurat:Decimal | None
    kat:str | None
    kat_bidang:str | None
    kat_proyek:str | None
    ptsk:str | None
    penampung:str | None
    no_sk:str | None
    status_sk:str | None
    manager:str | None
    sales:str | None
    mediator:str | None
    proses:str | None
    status:str | None
    group:str | None
    no_peta:str | None
    desa:str | None
    project:str | None

class BidangShpExSch(BaseGeoModel):
    n_idbidang:str | None
    o_idbidang:str | None
    pemilik:str | None
    code_desa:str | None
    dokumen:str | None
    sub_surat:str | None
    alashak:str | None
    luassurat:str | None
    kat:str | None
    kat_bidang:str | None
    kat_proyek:str | None
    ptsk:str | None
    penampung:str | None
    no_sk:str | None
    status_sk:str | None
    manager:str | None
    sales:str | None
    mediator:str | None
    proses:str | None
    status:str | None
    group:str | None
    no_peta:str | None
    desa:str | None
    project:str | None

class BidangSrcSch(SQLModel):
    id:UUID
    id_bidang:str

class BidangGetAllSch(SQLModel):
    id:UUID|None
    id_bidang:str|None

class BidangForTreeReportSch(SQLModel):
    id:UUID|None
    id_bidang:str|None
    id_bidang_lama:str|None
    alashak:str|None
    ptsk_id:UUID|None
    ptsk_name:str|None
    desa_id:UUID|None
    desa_name:str|None
    project_id:UUID|None
    project_name:str|None