from sqlmodel import SQLModel, Field, Relationship
from models.peminjaman_penggarap_model import PeminjamanPenggarapBase, PeminjamanPenggarapFullBase
from uuid import UUID

class PeminjamanPenggarapCreateSch(PeminjamanPenggarapBase):
    pass

class PeminjamanPenggarapSch(PeminjamanPenggarapBase):
    pass

class PeminjamanPenggarapByIdSch(PeminjamanPenggarapFullBase):
    pass

class PeminjamanPenggarapUpdateSch(PeminjamanPenggarapBase):
    pass

