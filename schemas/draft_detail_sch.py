from models.draft_model import DraftDetailBase, DraftDetailRawBase, DraftDetailFullBase
from common.as_form import as_form
from common.partial import optional
from sqlmodel import Field

@as_form
class DraftDetailCreateSch(DraftDetailBase):
    pass

class DraftDetailRawSch(DraftDetailRawBase):
    id_bidang:str | None = Field(alias="id_bidang")
    id_bidang_lama:str | None = Field(alias="id_bidang_lama")
    jenis_bidang:str | None = Field(alias="jenis_bidang")
    pemilik_name:str | None = Field(alias="pemilik_name")
    alashak:str | None = Field(alias="alashak")
    image_png:str | None = Field(alias="image_png")

class DraftDetailSch(DraftDetailFullBase):
    updated_by_name:str|None = Field(alias="updated_by_name")

@as_form
@optional
class DraftDetailUpdateSch(DraftDetailBase):
    pass