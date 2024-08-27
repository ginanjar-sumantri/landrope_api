from models.peminjaman_bidang_model import PeminjamanBidang, PeminjamanBidangBase, PeminjamanBidangFullBase
from typing import List
from schemas.kontak_sch import KontakCreateExtSch
from schemas.rekening_sch import RekeningCreateExtSch

class PeminjamanBidangCreateSch(PeminjamanBidang):
    pass

class PeminjamanBidangSch(PeminjamanBidangFullBase):
    pass

class PeminjamanBidangByIdSch(PeminjamanBidangFullBase):
    pass

class PeminjamanBidangUpdateSch(PeminjamanBidangBase):
    pass

