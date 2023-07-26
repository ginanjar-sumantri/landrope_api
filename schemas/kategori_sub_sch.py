from models.kategori_model import KategoriSub, KategoriSubBase, KategoriSubFullBase
from common.partial import optional
from sqlmodel import Field

class KategoriSubCreateSch(KategoriSubBase):
    pass

class KategoriSubSch(KategoriSubFullBase):
    kategori_name:str|None = Field(alias="kategori_name")

@optional
class KategoriSubUpdateSch(KategoriSubBase):
    pass