from models.kjb_model import KjbHarga, KjbHargaBase, KjbHargaFullBase
from schemas.kjb_termin_sch import KjbTerminCreateExtSch
from common.partial import optional
from pydantic import BaseModel
from typing import List
from uuid import UUID
from common.enum import JenisAlashakEnum
from decimal import Decimal

class KjbHargaCreateSch(KjbHargaBase):
    pass

class KjbHargaCreateExtSch(BaseModel):
    jenis_alashak:JenisAlashakEnum
    harga_akta:Decimal | None
    harga_transaksi:Decimal

    termins:list[KjbTerminCreateExtSch]

class KjbHargaSch(KjbHargaFullBase):
    pass

@optional
class KjbHargaUpdateSch(KjbHargaFullBase):
    pass