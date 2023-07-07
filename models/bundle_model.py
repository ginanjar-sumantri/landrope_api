from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.planing_model import Planing
    from models.dokumen_model import Dokumen
    from models.kjb_model import KjbDt

class BundleHdBase(SQLModel):
    code:str | None = Field(nullable=False)
    keyword:str | None = Field(default="")

    planing_id:UUID | None = Field(default=None, foreign_key="planing.id", nullable=True)

class BundleHdFullBase(BaseUUIDModel, BundleHdBase):
    pass

class BundleHd(BundleHdFullBase, table=True):
    planing:"Planing" = Relationship(back_populates="bundlehds", sa_relationship_kwargs={'lazy':'selectin'})
    bundledts:list["BundleDt"] = Relationship(back_populates="bundlehd", sa_relationship_kwargs={'lazy':'selectin'})
    kjb_dt:"KjbDt" = Relationship(back_populates="bundlehd", sa_relationship_kwargs={'lazy':'selectin'})
    

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
        return self.planing.name or ""
    
    @property
    def project_name(self) -> str | None:
        return self.planing.project.name or ""
    
    @property
    def desa_name(self) -> str | None:
        return self.planing.desa.name or ""

class BundleDtBase(SQLModel):
    code:str | None = Field(nullable=False)
    meta_data:str | None
    history_data:str | None
    bundle_hd_id:UUID | None = Field(default=None, foreign_key="bundle_hd.id", nullable=False)
    dokumen_id:UUID | None = Field(default=None, foreign_key="dokumen.id", nullable=False)

class BundleDtFullBase(BaseUUIDModel, BundleDtBase):
    pass

class BundleDt(BundleDtFullBase, table=True):
    bundlehd:"BundleHd" = Relationship(back_populates="bundledts", sa_relationship_kwargs={'lazy':'selectin'})
    dokumen:"Dokumen" = Relationship(sa_relationship_kwargs={'lazy':'selectin'})

    @property
    def dokumen_name(self) -> str | None:
        return self.dokumen.name
    
    @property
    def get_bundling_detail_code(self) -> str|None:
        bundling_code = self.bundlehd.get_bundling_code

        bundling_dt_code = f"{bundling_code}{self.dokumen.code}"

        return bundling_dt_code