from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from common.enum import JenisAlashakEnum, KategoriPenjualEnum, StatusValidEnum, StatusPetaLokasiEnum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.kjb_model import KjbHd, KjbDt
    from models.master_model import JenisSurat
    from models.notaris_model import Notaris
    from models.planing_model import Planing
    from models.dokumen_model import Dokumen

class TandaTerimaNotarisHdBase(SQLModel):
    kjb_hd_id:UUID = Field(nullable=False, foreign_key="kjb_hd.id")
    kjb_dt_id:UUID = Field(nullable=False, foreign_key="kjb_dt.id")
    jenis_alashak:JenisAlashakEnum
    jenis_surat_id:UUID = Field(foreign_key="jenis_surat.id", nullable=False)
    tanggal_tanda_terima:datetime | None = Field(default=datetime.now())
    nomor_tanda_terima:str
    kategori_penjual:KategoriPenjualEnum
    notaris_id:UUID = Field(nullable=False, foreign_key="notaris.id")
    planing_id:UUID = Field(nullable=False, foreign_key="planing.id")
    luas_surat:Decimal
    status_valid:StatusValidEnum
    status_peta_lokasi:StatusPetaLokasiEnum


class TandaTerimaNotarisHdFullBase(BaseUUIDModel, TandaTerimaNotarisHdBase):
    pass

class TandaTerimaNotarisHd(TandaTerimaNotarisHdFullBase, table=True):
    kjb_hd:"KjbHd" = Relationship(back_populates="tanda_terima_notaris_hd", sa_relationship_kwargs={'lazy':'selectin'})
    kjb_dt:"KjbDt" = Relationship(back_populates="tanda_terima_notaris_hd", sa_relationship_kwargs={'lazy':'selectin'})
    jenis_surat:"JenisSurat" = Relationship(back_populates="tanda_terima_notaris_hd", sa_relationship_kwargs={'lazy':'selectin'})
    notaris:"Notaris" = Relationship(back_populates="tanda_terima_notaris_hd", sa_relationship_kwargs={'lazy':'selectin'})
    planing:"Planing" = Relationship(back_populates="tanda_terima_notaris_hd", sa_relationship_kwargs={'lazy':'selectin'})

    tanda_terima_notaris_dts:list["TandaTerimaNotarisDt"] = Relationship(back_populates="tanda_terima_notaris_hd", sa_relationship_kwargs={'lazy':'selectin'})


class TandaTerimaNotarisDtBase(SQLModel):
    tanggal_tanda_terima:datetime | None = Field(default=datetime.now())
    dokumen_id:UUID = Field(foreign_key="dokumen.id")
    meta_data:str | None
    tanggal_terima_dokumen:datetime | None = Field(default=datetime.now())

    tanda_terima_notaris_hd_id:UUID = Field(foreign_key="tanda_terima_notaris_hd.id", nullable=False)
    
class TandaTerimaNotarisDtFullBase(BaseUUIDModel, TandaTerimaNotarisDtBase):
    pass

class TandaTerimaNotarisDt(TandaTerimaNotarisDtFullBase, table=True):
    dokumen:"Dokumen" = Relationship(back_populates="tanda_terima_notaris_dts", sa_relationship_kwargs={'lazy':'selectin'})
    tanda_terima_notaris_hd:"TandaTerimaNotarisHd" = Relationship(back_populates="tanda_terima_notaris_dts", sa_relationship_kwargs={'lazy':'selectin'})


