from models.bidang_model import BidangBase, BidangRawBase, BidangFullBase
from models.base_model import BaseGeoModel
from schemas.kjb_termin_sch import KjbTerminInSpkSch
from schemas.kjb_beban_biaya_sch import KjbBebanBiayaSch
from schemas.checklist_kelengkapan_dokumen_dt_sch import ChecklistKelengkapanDokumenDtSch
from schemas.bidang_overlap_sch import BidangOverlapForTahap, BidangOverlapRawSch
from schemas.beban_biaya_sch import BebanBiayaForSpkSch
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

class BidangSch(BidangFullBase):
    # created_by_name:str|None = Field(alias="created_by_name")
    # updated_by_name:str|None = Field(alias="updated_by_name")
    # pemilik_name:str|None = Field(alias="pemilik_name")
    # project_name:str|None = Field(alias="project_name")
    # desa_name:str|None = Field(alias="desa_name")
    # sub_project_name:str|None = Field(alias="sub_project_name")
    # planing_name:str|None = Field(alias="planing_name")
    # jenis_surat_name:str|None = Field(alias="jenis_surat_name")
    # kategori_name:str|None = Field(alias="kategori_name")
    # kategori_sub_name:str|None = Field(alias="kategori_sub_name")
    # kategori_proyek_name:str|None = Field(alias="kategori_proyek_name")
    # ptsk_name:str|None = Field(alias="ptsk_name")
    # no_sk:str|None = Field(alias="no_sk")
    # status_sk:str|None = Field(alias="status_sk")
    # penampung_name:str|None = Field(alias="penampung_name")
    # manager_name:str|None = Field(alias="manager_name")
    # sales_name:str|None = Field(alias="sales_name")
    # notaris_name:str|None = Field(alias="notaris_name")
    pass


class BidangRawSch(BidangRawBase):
    pemilik_name:str|None = Field(alias='pemilik_name')
    project_name:str|None = Field(alias='project_name')
    desa_name:str|None = Field(alias='desa_name')
    updated_by_name:str|None = Field(alias='updated_by_name')
    total_invoice:Decimal|None = Field(alias="total_invoice")
    total_harga_transaksi:Decimal|None = Field(alias="total_harga_transaksi")
    sisa_pelunasan:Decimal|None = Field(alias="sisa_pelunasan")
    biaya_lain:Decimal|None = Field(alias="biaya_lain")
    total_payment:Decimal|None = Field(alias="total_payment")
    nomor_tahap:int|None = Field(alias="nomor_tahap")
    status_sk:StatusSKEnum|None = Field(alias="status_sk")
    no_sk:str|None = Field(alias="no_sk")
    ptsk_name:str|None = Field(alias="ptsk_name")
    planing_name:str|None = Field(alias="planing_name")
    kota:str|None = Field(alias="kota")
    kecamatan:str|None = Field(alias="kecamatan")
    total_harga_transaksi:Decimal|None = Field(alias="total_harga_transaksi")
    sisa_pelunasan:Decimal|None = Field(alias="sisa_pelunasan")

class BidangListSch(BidangRawBase):
    total_harga_transaksi:Decimal|None = Field(alias="total_harga_transaksi")
    sisa_pelunasan:Decimal|None = Field(alias="sisa_pelunasan")

class BidangByIdSch(BidangRawBase):
    pemilik_name:str|None = Field(alias='pemilik_name')
    project_name:str|None = Field(alias='project_name')
    sub_project_name:str|None = Field(alias='sub_project_name')
    sub_project_code:str|None = Field(alias="sub_project_code")
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
    luas_gu_perorangan:Decimal | None
    luas_gu_pt:Decimal | None
    luas_pbt_perorangan:Decimal | None
    luas_pbt_pt:Decimal | None
    manager_name:str | None
    no_peta:str | None
    notaris_name:str | None
    ptsk_name:str | None
    status_sk:str | None
    bundle_hd_id:UUID | None
    ktp:str | None
    npwp:str | None
    percentage_lunas:Optional[int]
    sisa_pelunasan:Decimal | None
    jenis_alashak:JenisAlashakEnum | None
    termins:list[KjbTerminInSpkSch] | None

class BidangForSPKByIdExtSch(BidangForSPKByIdSch):
    
    beban_biayas:list[BebanBiayaForSpkSch] | None
    kelengkapan_dokumens:list[ChecklistKelengkapanDokumenDtSch] | None

class BidangByIdForTahapSch(BidangRawBase):
    project_name:Optional[str] = Field(alias="project_name")
    desa_name:Optional[str] = Field(alias="desa_name")
    planing_name:Optional[str] = Field(alias="planing_name")
    ptsk_name:Optional[str] = Field(alias="ptsk_name")
    ptsk_id:Optional[UUID] = Field(alias="ptsk_id")
    kjb_harga_akta:Optional[Decimal] = Field(alias="kjb_harga_akta")
    kjb_harga_transaksi:Optional[Decimal] = Field(alias="kjb_harga_transaksi")
    total_payment:Optional[Decimal] = Field(alias="total_payment")
    hasil_analisa_peta_lokasi:Optional[HasilAnalisaPetaLokasiEnum] = Field(alias="hasil_analisa_peta_lokasi")
    pemilik_name:Optional[str] = Field(alias="pemilik_name")
    overlaps:Optional[list[BidangOverlapRawSch]]

class BidangDraftChecklistDokumenSch(SQLModel):
    bundle_dt_id:UUID | None
    jenis_bayar:str | None
    dokumen_id:UUID | None

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
    kota:str | None
    kecamatan:str | None

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

class BidangForUtjSch(SQLModel):
    bidang_id:UUID
    id_bidang:Optional[str]
    alashak:Optional[str]
    luas_bayar:Optional[Decimal]
    luas_surat:Optional[Decimal]
    project_name:Optional[str]
    desa_name:Optional[str]

class BidangTotalBebanPenjualByIdSch(SQLModel):
    id:UUID
    id_bidang:Optional[str]
    total_beban_penjual:Optional[Decimal]

class BidangTotalInvoiceByIdSch(SQLModel):
    id:UUID
    id_bidang:Optional[str]
    total_invoice:Optional[Decimal]

class BidangPercentageLunasForSpk(SQLModel):
    bidang_id:Optional[UUID]
    percentage_lunas:Optional[Decimal]

class BidangIntersectionSch(SQLModel):
    id:UUID
    geom:str | None

class ReportBidangBintang(SQLModel):
    id_bidang:str|None
    id_bidang_lama:str|None
    alashak:str|None
    luas_surat:Decimal|None
    luas_damai:Decimal|None
    luas_batal:Decimal|None
    sudah_claim:Decimal|None #percentage
    belum_claim:Decimal|None #percentage
    sisa_bintang:Decimal|None

class BidangExcelSch(SQLModel):
    no:int | None
    id_bidang:str | None
    alias:str | None
    desa:str | None
    project:str | None
    ptsk:str | None
    pemilik:str | None
    alashak:str | None
    luas_surat:str | None
    luas_ukur:str | None
    luas_pbt:str | None
    luas_bayar:str | None
    harga_transaksi:str | None
    total_harga:str | None

class BidangRptExcel(SQLModel):
    id_bidang:str|None
    luas_surat:Decimal|None
    pemilik_name:str|None
    id_bidang_ov:str|None
    luas_ov:Decimal|None

class BidangFilterJson(SQLModel):
    id_bidang:str|None
    id_bidang_lama:str|None
    alashak:str|None
    pemilik_name:str|None
    project_name:str|None
    desa_name:str|None
    group:str|None
    no_peta:str|None
    nomor_tahap:str|None
    luas_surat:str|None
    status:str|None
    total_harga_transaksi:Decimal|None
    total_payment:Decimal|None
    sisa_pelunasan:Decimal|None

class BidangGpsValidator(SQLModel):
    id_bidang:str|None
    id_bidang_lama:str|None
    alashak:str|None
    pemilik_name:str|None
    project_name:str|None
    desa_name:str|None
    group:str|None
    no_peta:str|None
    luas_surat:Decimal|None

class BidangParameterDownload(SQLModel):
    projects:list[UUID]|None
    desas:list[UUID]|None
    jenis_bidangs:list[str]|None

#semua jenis pembayaran dan komponen biaya untuk tarikan excel
class BidangAllPembayaran(SQLModel):
    id_pembayaran:UUID|None
    name:str|None
    amount:Decimal|None