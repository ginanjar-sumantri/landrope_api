from models.peminjaman_header_model import PeminjamanHeaderBase, PeminjamanHeaderFullBase
from models.peminjaman_bidang_model import PeminjamanBidangBase
from typing import List

class PeminjamanHeaderCreateSch(PeminjamanHeaderBase):
    peminjaman_bidangs: List[PeminjamanBidangBase]

class PeminjamanHeaderSch(PeminjamanHeaderBase):
    pass

class PeminjamanHeaderByIdSch(PeminjamanHeaderFullBase):
    pass

class PeminjamanHeaderUpdateSch(PeminjamanHeaderBase):
    pass

