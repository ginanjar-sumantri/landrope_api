from models.bidang_overlap_model import BidangOverlap, BidangOverlapBase, BidangOverlapFullBase, BidangOverlapRawBase
from common.partial import optional
from common.as_form import as_form
from common.enum import KategoriOverlapEnum, JenisBidangEnum, TipeOverlapEnum
from sqlmodel import Field, SQLModel
from uuid import UUID
from decimal import Decimal

@as_form
class BidangOverlapCreateSch(BidangOverlapBase):
    pass

class BidangOverlapRawSch(BidangOverlapRawBase):
    id_bidang_intersect:str|None = Field(alias="id_bidang_intersect")
    alashak_intersect:str|None = Field(alias="alashak_intersect")
    luas_surat_intersect:str|None = Field(alias="luas_surat_intersect")
    jenis_bidang_intersect:JenisBidangEnum|None = Field(alias="jenis_bidang_intersect")
    tipe_overlap:TipeOverlapEnum|None = Field(alias="tipe_overlap")

class BidangOverlapSch(BidangOverlapFullBase):
    pass

@as_form
@optional
class BidangOverlapUpdateSch(BidangOverlapBase):
    pass

class BidangOverlapUpdateExtSch(SQLModel):
    id:UUID
    kategori:KategoriOverlapEnum|None
    harga_transaksi:Decimal|None
    luas_bayar:Decimal|None
    is_show:bool|None


class BidangOverlapForTahap(SQLModel):
    bidang_overlap_id:UUID
    bidang_id:UUID | None
    id_bidang:str | None
    luas_surat:Decimal | None
    luas_intersect:Decimal | None
    kategori:KategoriOverlapEnum | None
    harga_transaksi:Decimal | None

class BidangOverlapForPrintout(SQLModel):
    bidang_id:UUID|None
    ket:str|None
    nama:str|None
    alashak:str|None
    luas:Decimal|None
    luasExt:str|None
    luas_overlap:Decimal|None
    luas_overlapExt:str|None
    kat:str|None
    id_bidang:str|None
    status_overlap:str|None

