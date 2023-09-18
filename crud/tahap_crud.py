from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from crud.base_crud import CRUDBase
from models.tahap_model import Tahap
from schemas.tahap_sch import TahapCreateSch, TahapUpdateSch

class CRUDTahap(CRUDBase[Tahap, TahapCreateSch, TahapUpdateSch]):
   pass

tahap = CRUDTahap(Tahap)