from models.tanda_terima_notaris_model import TandaTerimaNotarisDt, TandaTerimaNotarisDtBase, TandaTerimaNotarisDtFullBase
from common.partial import optional
from common.as_form import as_form
from sqlmodel import Field

@as_form
class TandaTerimaNotarisDtCreateSch(TandaTerimaNotarisDtBase):
    pass

class TandaTerimaNotarisDtSch(TandaTerimaNotarisDtFullBase):
    dokumen_name:str | None = Field(alias="dokumen_name")
    nomor_tanda_terima:str | None = Field(alias="nomor_tanda_terima")
    updated_by_name:str|None = Field(alias="updated_by_name")

@as_form
@optional
class TandaTerimaNotarisDtUpdateSch(TandaTerimaNotarisDtBase):
    pass