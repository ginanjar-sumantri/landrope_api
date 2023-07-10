from models.tanda_terima_notaris_model import TandaTerimaNotarisDt, TandaTerimaNotarisDtBase, TandaTerimaNotarisDtFullBase
from common.partial import optional
from sqlmodel import Field

class TandaTerimaNotarisDtCreateSch(TandaTerimaNotarisDtBase):
    pass

class TandaTerimaNotarisDtSch(TandaTerimaNotarisDtFullBase):
    dokumen_name:str | None = Field(alias="dokumen_name")
    nomor_tanda_terima:str | None = Field(alias="nomor_tanda_terima")

@optional
class TandaTerimaNotarisDtUpdateSch(TandaTerimaNotarisDtBase):
    pass