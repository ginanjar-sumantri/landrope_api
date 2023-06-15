from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.sql import func
from crud.base_crud import CRUDBase
from models.desa_model import Desa
from schemas.desa_sch import DesaCreateSch, DesaUpdateSch, DesaSch
from typing import List

from datetime import datetime

class CRUDDesa(CRUDBase[Desa, DesaCreateSch, DesaUpdateSch]):
    pass

    
desa = CRUDDesa(Desa)