from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from common.enum import JenisAlashakEnum, KategoriPenjualEnum, StatusPetaLokasiEnum
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
    # kjb_hd_id:UUID = Field(nullable=False, foreign_key="kjb_hd.id")
    kjb_dt_id:UUID = Field(nullable=False, foreign_key="kjb_dt.id")
    tanggal_tanda_terima:datetime | None = Field(default=datetime.now())
    nomor_tanda_terima:str
    notaris_id:UUID = Field(nullable=False, foreign_key="notaris.id")
    planing_id:UUID | None = Field(nullable=True, foreign_key="planing.id")
    luas_surat:Decimal


class TandaTerimaNotarisHdFullBase(BaseUUIDModel, TandaTerimaNotarisHdBase):
    pass

class TandaTerimaNotarisHd(TandaTerimaNotarisHdFullBase, table=True):
    # kjb_hd:"KjbHd" = Relationship(back_populates="tanda_terima_notaris_hd", sa_relationship_kwargs={'lazy':'selectin'})
    kjb_dt:"KjbDt" = Relationship(back_populates="tanda_terima_notaris_hd", sa_relationship_kwargs={'lazy':'selectin'})
    notaris:"Notaris" = Relationship(sa_relationship_kwargs={'lazy':'selectin'})
    planing:"Planing" = Relationship(sa_relationship_kwargs={'lazy':'selectin'})

    tanda_terima_notaris_dts:list["TandaTerimaNotarisDt"] = Relationship(sa_relationship_kwargs={'lazy':'selectin'})

    @property
    def alahak(self) -> str:
        return self.kjb_dt.alashak
    
    @property
    def jenis_surat_name(self) -> str:
        return self.kjb_dt.jenis_surat.name
    
    @property
    def notaris_name(self) -> str:
        return self.notaris.name
    
    @property
    def planing_name(self) -> str:
        return self.planing.name



class TandaTerimaNotarisDtBase(SQLModel):
    tanggal_tanda_terima:datetime | None = Field(default=datetime.now())
    dokumen_id:UUID = Field(foreign_key="dokumen.id")
    meta_data:str | None
    tanggal_terima_dokumen:datetime | None = Field(default=datetime.now())

    tanda_terima_notaris_hd_id:UUID = Field(foreign_key="tanda_terima_notaris_hd.id", nullable=False)
    
class TandaTerimaNotarisDtFullBase(BaseUUIDModel, TandaTerimaNotarisDtBase):
    pass

class TandaTerimaNotarisDt(TandaTerimaNotarisDtFullBase, table=True):
    dokumen:"Dokumen" = Relationship(sa_relationship_kwargs={'lazy':'selectin'})
    tanda_terima_notaris_hd:"TandaTerimaNotarisHd" = Relationship(back_populates="tanda_terima_notaris_dts", sa_relationship_kwargs={'lazy':'selectin'})


