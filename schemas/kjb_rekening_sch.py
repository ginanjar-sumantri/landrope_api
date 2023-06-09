from models.kjb_model import KjbRekening, KjbRekeningBase, KjbRekeningFullBase
from common.partial import optional
from pydantic import BaseModel
from typing import List
from uuid import UUID

class KjbRekeningCreateSch(KjbRekeningBase):
    pass

class KjbRekeningCreateExtSch(BaseModel):
    nama_pemilik_rekening:str
    bank_rekening:str
    nomor_rekening:str

class KjbRekeningSch(KjbRekeningFullBase):
    pass

@optional
class KjbRekeningUpdateSch(KjbRekeningBase):
    pass