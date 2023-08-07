from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from models.planing_model import Planing
    from models.dokumen_model import Dokumen
    from models.kjb_model import KjbDt
    from models.worker_model import Worker

class BundleHdBase(SQLModel):
    code:str | None = Field(nullable=False)
    keyword:str | None = Field(default="")

    planing_id:UUID | None = Field(default=None, foreign_key="planing.id", nullable=True)

class BundleHdFullBase(BaseUUIDModel, BundleHdBase):
    pass

class BundleHd(BundleHdFullBase, table=True):
    planing:"Planing" = Relationship(sa_relationship_kwargs={'lazy':'selectin'})
    bundledts:list["BundleDt"] = Relationship(back_populates="bundlehd", sa_relationship_kwargs={'lazy':'selectin'})
    kjb_dt:"KjbDt" = Relationship(back_populates="bundlehd", sa_relationship_kwargs={'lazy':'joined',
                                                                                                    'uselist':'False',
                                                                                     'primaryjoin':'BundleHd.id==KjbDt.bundle_hd_id'})
    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "BundleHd.updated_by_id==Worker.id",
        }
    )
    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)
    

    @property
    def get_bundling_code(self)-> str | None:
        bundle_code = self.code
        project_code = self.planing.project.code
        desa_code = self.planing.desa.code

        codes = [project_code, desa_code, bundle_code]

        bunddling_code = f"D" + "".join(codes)

        return bunddling_code
    
    @property
    def planing_name(self) -> str | None:
        if self.planing is None:
            return ""
        return self.planing.name or ""
    
    @property
    def project_name(self) -> str | None:
        if self.planing is None:
            return ""
        return self.planing.project.name or ""
    
    @property
    def desa_name(self) -> str | None:
        if self.planing is None:
            return ""
        return self.planing.desa.name or ""
    
    @property
    def alashak(self) -> str | None:
        if self.kjb_dt is None:
            return None
        
        print(self.kjb_dt.id)
        
        return self.kjb_dt.alashak

# -----------------------------------------------------------------------------------------------

class BundleDtBase(SQLModel):
    code:str | None = Field(nullable=False)
    meta_data:str | None
    history_data:str | None
    bundle_hd_id:UUID | None = Field(default=None, foreign_key="bundle_hd.id", nullable=False)
    dokumen_id:UUID | None = Field(default=None, foreign_key="dokumen.id", nullable=False)
    file_path:str | None = Field(nullable=True)
    riwayat_data:str | None = Field(nullable=True)

class BundleDtFullBase(BaseUUIDModel, BundleDtBase):
    pass

class BundleDt(BundleDtFullBase, table=True):
    bundlehd:"BundleHd" = Relationship(back_populates="bundledts", sa_relationship_kwargs={'lazy':'select'})
    dokumen:"Dokumen" = Relationship(sa_relationship_kwargs={'lazy':'selectin'})
    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "BundleDt.updated_by_id==Worker.id",
        }
    )

    class Meta:
        order_fields = {
            # 'all' : True,
            # 'all_join': False,
            'dokumen_name' : 'dokumen.name'
        }

    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)

    @property
    def dokumen_name(self) -> str | None:
        return self.dokumen.name
    
    @property
    def file_exists(self) -> bool:
        if self.file_path:
            return True
        
        return False
    
    @property
    def have_riwayat(self) -> bool:

        return getattr(getattr(self, 'dokumen', False), 'is_riwayat', False)
    
    @property
    def dyn_form(self) -> str | None:
        return getattr(getattr(self, 'dokumen', None), 'dyn_form', None)
    
    @property
    def kategori_dokumen_name(self) -> str | None:
        return getattr(getattr(getattr(self, 'dokumen', None), 'kategori_dokumen', None), 'name', None)