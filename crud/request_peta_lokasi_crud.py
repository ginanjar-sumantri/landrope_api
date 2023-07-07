from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.sql import func
from crud.base_crud import CRUDBase
from models.request_peta_lokasi_model import RequestPetaLokasi
from schemas.request_peta_lokasi_sch import RequestPetaLokasiCreateSch, RequestPetaLokasiUpdateSch, RequestPetaLokasiSch
from typing import List

from datetime import datetime

class CRUDRequestPetaLokasi(CRUDBase[RequestPetaLokasi, RequestPetaLokasiCreateSch, RequestPetaLokasiUpdateSch]):
    pass

    
request_peta_lokasi = CRUDRequestPetaLokasi(RequestPetaLokasi)