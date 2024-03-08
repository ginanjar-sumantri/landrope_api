from models.kjb_model import KjbDt, KjbDtBase, KjbDtFullBase
from common.partial import optional
from common.enum import JenisAlashakEnum, PosisiBidangEnum, StatusSKEnum, HasilAnalisaPetaLokasiEnum, ProsesBPNOrderGambarUkurEnum, StatusPetaLokasiEnum, WorkflowLastStatusEnum
from sqlmodel import Field, SQLModel
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime, date

class KjbDtCreateSch(KjbDtBase):
    pass

class KjbDtCreateExtSch(SQLModel):
    id:UUID|None
    jenis_alashak:JenisAlashakEnum | None
    alashak:str | None
    posisi_bidang:PosisiBidangEnum | None
    harga_akta:Decimal | None
    harga_transaksi:Decimal | None
    luas_surat:Decimal | None
    desa_id:Optional[UUID] 
    project_id:Optional[UUID] 
    pemilik_id:UUID | None 
    jenis_surat_id:UUID | None
    jumlah_waris:int | None

class KjbDtSch(KjbDtFullBase):
    kjb_code:str | None = Field(alias="kjb_code")
    jenis_surat_name:str | None = Field(alias="jenis_surat_name")
    desa_name:str | None = Field(alias="desa_name")
    desa_name_by_ttn:str | None = Field(alias="desa_name_by_ttn")
    project_name:str | None = Field(alias="project_name")
    project_name_by_ttn:str | None = Field(alias="project_name_by_ttn")
    kategori_penjual:str | None = Field(alias="kategori_penjual")
    done_request_petlok:bool | None = Field(alias="done_request_petlok")
    pemilik_name:str | None = Field(alias="pemilik_name")
    nomor_telepon:List[str] | None = Field(alias="nomor_telepon")
    updated_by_name:str|None = Field(alias="updated_by_name")
    kjb_hd_group:str|None
    gu_exists:bool|None = Field(default=False)
    pbt_exists:bool|None = Field(default=False)
    step_name_workflow: str | None
    status_workflow: WorkflowLastStatusEnum | None

class KjbDtListRequestPetlokSch(KjbDtSch):
    has_input_petlok:bool | None = Field(alias="has_input_petlok")
    bundle_dt_alashak_id:UUID | None
    bundle_dt_alashak_file_exists:bool | None
    bundle_dt_alashak_file_path:str | None
    tanggal_terima_berkas:date | None
    tanggal_pengukuran:date |None
    penunjuk_batas:str | None
    surveyor:str | None 
    tanggal_kirim_ukur:date|None 
    keterangan_req_petlok_name:str|None

class KjbDtListSch(SQLModel):
    kjb_code:str|None
    kjb_hd_id:UUID|None
    id:UUID|None
    alashak:str|None
    jenis_alashak:JenisAlashakEnum|None
    harga_akta:Decimal|None
    harga_transaksi:Decimal|None
    status_peta_lokasi:StatusPetaLokasiEnum|None
    luas_surat:Decimal|None
    luas_surat_by_ttn:Decimal|None
    created_at:datetime|None
    harga_standard:Decimal|None
    step_name_workflow: str | None
    status_workflow: WorkflowLastStatusEnum | None
    

@optional
class KjbDtUpdateSch(KjbDtBase):
    pass

class KjbDtSrcForGUSch(SQLModel):
    kjb_dt_id:UUID | None
    kjb_dt_alashak:str | None
    bidang_id:UUID | None
    id_bidang:str | None

class KjbDtForOrderGUById(SQLModel):
    id:UUID | None
    id_bidang:str | None
    jenis_alashak:JenisAlashakEnum | None
    alashak:str | None
    status_sk:StatusSKEnum | None
    ptsk_name:str | None
    hasil_analisa_peta_lokasi:HasilAnalisaPetaLokasiEnum | None
    proses_bpn_order_gu:ProsesBPNOrderGambarUkurEnum | None
    luas_surat:Decimal | None

class KjbDtForCloud(SQLModel):
    id:UUID
    kjb_hd_id:Optional[UUID]
    group:Optional[str]
    jenis_alashak:Optional[JenisAlashakEnum]
    jenis_surat_id:Optional[UUID]
    alashak:Optional[str]
    harga_akta:Optional[Decimal]
    harga_transaksi:Optional[Decimal]
    bundle_hd_id:Optional[UUID]

class KjbDtForUtjKhususSch(SQLModel):
    id:UUID
    id_bidang:Optional[str]
    alashak:Optional[str]
    luas_bayar:Optional[Decimal]
    luas_surat:Optional[Decimal]
    luas_surat_by_ttn:Optional[Decimal]