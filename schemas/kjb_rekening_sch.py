from models.kjb_model import KjbRekening, KjbRekeningBase, KjbRekeningFullBase
from common.partial import optional
from sqlmodel import SQLModel
from typing import List
from uuid import UUID

class KjbRekeningCreateSch(KjbRekeningBase):
    pass

class KjbRekeningCreateExtSch(SQLModel):
    id:UUID|None
    nama_pemilik_rekening:str|None
    bank_rekening:str|None
    nomor_rekening:str|None
    pemilik_id:UUID|None

class KjbRekeningSch(KjbRekeningFullBase):
    pass

@optional
class KjbRekeningUpdateSch(KjbRekeningBase):
    pass