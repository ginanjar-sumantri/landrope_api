from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from crud.base_crud import CRUDBase
from models.planing_model import Planing
from schemas.planing_sch import PlaningCreateSch, PlaningUpdateSch

class CRUDPlaning(CRUDBase[Planing, PlaningCreateSch, PlaningUpdateSch]):
    pass

planing = CRUDPlaning(Planing)