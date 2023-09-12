from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING
from common.enum import JenisBayarEnum

if TYPE_CHECKING:
    from models.dokumen_model import Dokumen
    from models.worker_model import Worker
    from models.bidang_model import Bidang
    from models.bundle_model import BundleDt

class ChecklistKelengkapanDokumenHdBase(SQLModel):
    bidang_id:UUID = Field(nullable=False, foreign_key="bidang.id")
    
class ChecklistKelengkapanDokumenHdFullBase(BaseUUIDModel, ChecklistKelengkapanDokumenHdBase):
    pass

class ChecklistKelengkapanDokumenHd(ChecklistKelengkapanDokumenHdFullBase, table=True):
    details:list["ChecklistKelengkapanDokumenDt"] = Relationship(
        back_populates="checklist_kelengkapan_dokumen_hd",
        sa_relationship_kwargs=
        {
            'lazy' : 'selectin',
            "cascade" : "delete, all",
            "foreign_keys" : "[ChecklistKelengkapanDokumenDt.checklist_kelengkapan_dokumen_hd_id]"
        }
    )

    bidang:"Bidang" = Relationship(
        sa_relationship_kwargs=
        {
            'lazy' : 'selectin'
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
    
    @property
    def id_bidang(self) -> str | None :
        return getattr(getattr(self, "bidang", None), "id_bidang", None)
    
    @property
    def jenis_alashak(self) -> str | None :
        return getattr(getattr(self, "bidang", None), "jenis_alashak", None)
    
    @property
    def alashak(self) -> str | None :
        return getattr(getattr(self, "bidang", None), "alashak", None)
    
    @property
    def bundle_hd_code(self) -> str | None :
        return getattr(getattr(getattr(self, "bidang", None), "bundlehd", None), "code", None)
    
    @property
    def bundle_hd_id(self) -> str | None :
        return getattr(getattr(getattr(self, "bidang", None), "bundlehd", None), "id", None)

    

    
########################################################################

class ChecklistKelengkapanDokumenDtBase(SQLModel):
    checklist_kelengkapan_dokumen_hd_id:UUID = Field(nullable=False, foreign_key="checklist_kelengkapan_dokumen_hd.id")
    bundle_dt_id:UUID = Field(foreign_key="bundle_dt.id")
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

    bundle_dt:"BundleDt" = Relationship(
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
    
    @property
    def dokumen_name(self) -> str | None:
        return getattr(getattr(self, "dokumen", None), "name", None)
    
    @property
    def has_meta_data(self) -> bool | None:
        if self.bundle_dt is None:
            return False
        
        return self.bundle_dt.file_exists
    
            

    