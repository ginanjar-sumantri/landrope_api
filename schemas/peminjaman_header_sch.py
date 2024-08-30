from sqlmodel import SQLModel, Field, Relationship
from models.peminjaman_header_model import PeminjamanHeaderBase, PeminjamanHeaderFullBase
from models.peminjaman_bidang_model import PeminjamanBidangBase
from typing import List
from decimal import Decimal


class PeminjamanHeaderCreateSch(PeminjamanHeaderBase):
    peminjaman_bidangs: List[PeminjamanBidangBase] | None
   
class PeminjamanHeaderSch(PeminjamanHeaderFullBase):    
    pass

class PeminjamanHeaderByIdSch(PeminjamanHeaderFullBase):
    peminjaman_bidangs: List[PeminjamanBidangBase] | None

class PeminjamanHeaderUpdateSch(PeminjamanHeaderFullBase):
    peminjaman_bidangs: List[PeminjamanBidangBase] | None






