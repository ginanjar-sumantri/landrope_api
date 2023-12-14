from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING, Optional
from common.enum import JenisAlashakEnum, SatuanBayarEnum, SatuanHargaEnum
from decimal import Decimal
from pydantic import condecimal

if TYPE_CHECKING:
    from models.planing_model import Planing
    from models.worker_model import Worker

class BebanBiayaBase(SQLModel):
    name:Optional[str] = Field(nullable=True)
    is_active:Optional[bool] = Field(nullable=True)
    is_tax:Optional[bool] = Field(nullable=True)
    is_edit:Optional[bool] = Field(nullable=True)
    is_add_pay:Optional[bool] = Field(nullable=True)
    formula:Optional[str] = Field(nullable=True)
    satuan_bayar:Optional[SatuanBayarEnum] = Field(nullable=True)
    satuan_harga:Optional[SatuanHargaEnum] = Field(nullable=True)
    amount:Optional[condecimal(decimal_places=2)] = Field(nullable=True)

class BebanBiayaFullBase(BebanBiayaBase, BaseUUIDModel):
    pass

class BebanBiaya(BebanBiayaFullBase, table=True):
    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "BebanBiaya.updated_by_id==Worker.id",
        }
    )
    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)

#####################################################

class JenisLahanBase(SQLModel):
    code:str = Field(max_length=50)
    name:str = Field(max_length=150)

class JenisLahan(BaseUUIDModel, JenisLahanBase, table=True):
    pass
    # bidangs: "Bidang" = Relationship(back_populates="jenis_lahan", sa_relationship_kwargs={'lazy':'selectin'})

######################################################
class JenisSuratBase(SQLModel):
    jenis_alashak:JenisAlashakEnum
    name:str

class JenisSurat(BaseUUIDModel, JenisSuratBase, table=True):
    pass

    # kjb_dts: list["KjbDt"] = Relationship(back_populates="jenis_surat", sa_relationship_kwargs={'lazy':'select'})
    # tanda_terima_notaris_hd:list["TandaTerimaNotarisHd"] = Relationship(back_populates="jenis_surat", sa_relationship_kwargs={'lazy':'selectin'})
    
#######################################################

class HargaStandardBase(SQLModel):
    planing_id:UUID = Field(nullable=False, foreign_key="planing.id")
    harga:Decimal | None

class HargaStandardFullBase(HargaStandardBase, BaseUUIDModel):
    pass

class HargaStandard(HargaStandardFullBase, table=True):
    planing:"Planing" = Relationship(sa_relationship_kwargs={'lazy':'selectin'})
    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "HargaStandard.updated_by_id==Worker.id",
        }
    )
    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)

    @property
    def planing_name(self) -> str :
        if self.planing is None:
            return ""
        
        return self.planing.name
    
    @property
    def planing_code(self) -> str :
        if self.planing is None:
            return ""
        
        return self.planing.code
