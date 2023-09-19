from models.bidang_komponen_biaya_model import BidangKomponenBiaya, BidangKomponenBiayaBase, BidangKomponenBiayaFullBase
from common.partial import optional
from common.as_form import as_form
from sqlmodel import SQLModel, Field

class BidangKomponenBiayaCreateSch(BidangKomponenBiayaBase):
    pass

class BiayaKomponenBiayaSch(BidangKomponenBiayaFullBase):
    updated_by_name:str|None = Field(alias="updated_by_name")

@optional
class BiayaKomponenBiayaUpdateSch(BidangKomponenBiayaBase):
    pass