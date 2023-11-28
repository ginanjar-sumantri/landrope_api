from models.bidang_model import BidangHistoryBase, BidangHistoryFullBase, BidangHistoryBaseExt
from common.partial import optional
from common.enum import JenisBidangEnum, StatusBidangEnum, JenisAlashakEnum
from typing import Optional
from sqlmodel import Field, SQLModel
from uuid import UUID
from decimal import Decimal
from datetime import datetime


class BidangHistoryCreateSch(BidangHistoryBaseExt):
    pass

class BidangHistorySch(BidangHistoryFullBase):
    trans_worker_name:str|None = Field(alias="trans_worker_name")

class MetaDataSch(SQLModel):
    id: UUID 
    updated_at : datetime | None 
    created_at : datetime | None 
    created_by_id: UUID | None 
    updated_by_id: UUID | None
    id_bidang:Optional[str] 
    id_bidang_lama:Optional[str] 
    no_peta:Optional[str]
    pemilik_id:Optional[UUID]
    jenis_bidang:JenisBidangEnum | None
    status:StatusBidangEnum | None
    planing_id:Optional[UUID] 
    sub_project_id:Optional[UUID] 
    group:Optional[str]
    jenis_alashak:Optional[JenisAlashakEnum] 
    jenis_surat_id:Optional[UUID]
    alashak:Optional[str] 
    kategori_id:Optional[UUID] 
    kategori_sub_id:Optional[UUID] 
    kategori_proyek_id:Optional[UUID] 
    skpt_id:Optional[UUID] 
    penampung_id:Optional[UUID]
    manager_id:Optional[UUID]
    sales_id:Optional[UUID]
    mediator:Optional[str] 
    telepon_mediator:Optional[str]
    notaris_id:Optional[UUID] 
    tahap:Optional[int] 
    informasi_tambahan:Optional[str] 
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
    bundle_hd_id:UUID | None
    geom:str | None
    geom_ori:str | None
    
    created_by_name:str|None
    updated_by_name:str|None
    pemilik_name:str|None
    project_name:str|None
    desa_name:str|None
    sub_project_name:str|None
    planing_name:str|None
    jenis_surat_name:str|None
    kategori_name:str|None
    kategori_sub_name:str|None
    kategori_proyek_name:str|None
    ptsk_name:str|None
    no_sk:str|None
    status_sk:str|None
    penampung_name:str|None
    manager_name:str|None
    sales_name:str|None
    notaris_name:str|None