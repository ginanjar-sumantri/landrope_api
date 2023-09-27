from models.bundle_model import BundleDt, BundleDtBase, BundleDtFullBase
from common.partial import optional
from common.as_form import as_form
from sqlmodel import Field, SQLModel
from typing import Optional
from uuid import UUID

class BundleDtCreateSch(BundleDtBase):
    pass

class BundleDtSch(BundleDtFullBase):
    dokumen_name:str | None = Field(alias="dokumen_name")
    file_exists:bool | None = Field(alias="file_exists")
    have_riwayat:bool | None = Field(alias="have_riwayat")
    updated_by_name:str | None = Field(alias="updated_by_name")
    kategori_dokumen_name:str | None = Field(alias="kategori_dokumen_name")

class BundleDtMetaDynSch(SQLModel):
    meta_data:str|None
    dyn_form:str|None = Field(alias="dyn_form")

@as_form
@optional
class BundleDtUpdateSch(BundleDtBase):
    pass

class BundleDtMetaData(SQLModel):
    bidang_id:Optional[UUID]
    id_bidang:Optional[str]
    meta_data:Optional[str]
    key_field:Optional[str]

class BundleDtForCloud(SQLModel):
    id:UUID