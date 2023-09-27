from models.kjb_model import KjbHarga, KjbHargaBase, KjbHargaFullBase
from schemas.kjb_termin_sch import KjbTerminCreateExtSch, KjbTerminSch
from common.partial import optional
from pydantic import BaseModel
from typing import List
from uuid import UUID
from common.enum import JenisAlashakEnum
from decimal import Decimal
from sqlmodel import SQLModel
from typing import Optional

class KjbHargaCreateSch(KjbHargaBase):
    termins:list[KjbTerminCreateExtSch]

class KjbHargaCreateExtSch(BaseModel):
    jenis_alashak:JenisAlashakEnum
    harga_akta:Decimal | None
    harga_transaksi:Decimal

    termins:list[KjbTerminCreateExtSch]

class KjbHargaSch(KjbHargaFullBase):
    pass

class KjbHargaExtSch(KjbHargaFullBase):
    termins:list[KjbTerminSch]

@optional
class KjbHargaUpdateSch(KjbHargaFullBase):
    pass

class KjbHargaForCloud(SQLModel):
    id:UUID
    harga_akta:Optional[Decimal]
    harga_transaksi:Optional[Decimal]