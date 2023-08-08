from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from sqlalchemy import exc
from sqlmodel.ext.asyncio.session import AsyncSession
from crud.base_crud import CRUDBase
from models.desa_model import Desa
from models.code_counter_model import CodeCounterEnum
from schemas.desa_sch import DesaCreateSch, DesaUpdateSch, DesaSch
from common.generator import generate_code
from typing import List
from uuid import UUID

from datetime import datetime

class CRUDDesa(CRUDBase[Desa, DesaCreateSch, DesaUpdateSch]):
    pass

    
desa = CRUDDesa(Desa)