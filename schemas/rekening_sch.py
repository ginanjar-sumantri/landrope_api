from models.pemilik_model import RekeningBase, RekeningFullBase
from common.partial import optional
from typing import List
from pydantic import BaseModel

class RekeningCreateSch(RekeningBase):
    pass

class RekeningCreateExtSch(BaseModel):
    nama_pemilik_rekening:str | None
    bank_rekening:str | None
    nomor_rekening:str | None

class RekeningSch(RekeningFullBase):
    pass

@optional
class RekeningUpdateSch(RekeningBase):
    pass