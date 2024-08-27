from models.peminjaman_header_model import PeminjamanHeader, PeminjamanHeaderBase, PeminjamanHeaderFullBase
from models.peminjaman_bidang_model import PeminjamanBidang
from typing import List
from schemas.kontak_sch import KontakCreateExtSch
from schemas.rekening_sch import RekeningCreateExtSch

class PeminjamanHeaderCreateSch(PeminjamanHeader):
    peminjaman_bidangs: list[PeminjamanBidang] | None

class PeminjamanHeaderSch(PeminjamanHeader):
    pass

class PeminjamanHeaderByIdSch(PeminjamanHeaderFullBase):
    pass

class PeminjamanHeaderUpdateSch(PeminjamanHeaderBase):
    pass

