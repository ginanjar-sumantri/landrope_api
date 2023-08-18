from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING
from common.enum import JenisAlashakEnum, JenisBayarEnum, KategoriPenjualEnum

if TYPE_CHECKING:
    from models.dokumen_model import Dokumen
    from models.worker_model import Worker
    from models.bidang_model import Bidang

class ChecklistKelengkapanDokumenHdBase(SQLModel):
    bidang_id:UUID = Field(nullable=False, foreign_key="bidang.id")
    
class ChecklistKelengkapanDokumenHdFullBase(BaseUUIDModel, ChecklistKelengkapanDokumenHdBase):
    pass

class ChecklistKelengkapanDokumenHd(ChecklistKelengkapanDokumenHdFullBase, table=True):
    details:"ChecklistKelengkapanDokumenDt" = Relationship(
        back_populates="checklist_kelengkapan_dokumen_hd",
        sa_relationship_kwargs=
        {
            'lazy' : 'selectin'
        }
    )

    bidang:"Bidang" = Relationship(
        sa_relationship_kwargs=
        {
            'lazy' : 'select'
        })
    
    worker: "Worker" = Relationship(  
        sa_relationship_kwargs=
        {
            "lazy": "joined",
            "primaryjoin": "ChecklistKelengkapanDokumenHd.updated_by_id==Worker.id",
        })
    
    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)
    
########################################################################

class ChecklistKelengkapanDokumenDtBase(SQLModel):
    checklist_kelengkapan_dokumen_hd_id:UUID = Field(nullable=False, foreign_key="checklist_kelengkapan_dokumen_hd.id")
    jenis_bayar:JenisBayarEnum
    dokumen_id:UUID = Field(default=None, foreign_key="dokumen.id")

class ChecklistKelengkapanDokumenDtFullBase(BaseUUIDModel, ChecklistKelengkapanDokumenDtBase):
    pass

class ChecklistKelengkapanDokumenDt(ChecklistKelengkapanDokumenDtFullBase, table=True):
    checklist_kelengkapan_dokumen_hd:"ChecklistKelengkapanDokumenHd" = Relationship(
        back_populates = "details",
        sa_relationship_kwargs = 
        {
            'lazy' : 'selectin'
        }
    )

    dokumen:"Dokumen" = Relationship(
        sa_relationship_kwargs =
        {
            'lazy':'select'
        })
    
    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "ChecklistKelengkapanDokumenDt.updated_by_id==Worker.id",
        }
    )
    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)

    