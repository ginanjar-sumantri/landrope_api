from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.kjb_model import KjbRekening
from schemas.kjb_rekening_sch import KjbRekeningCreateSch, KjbRekeningUpdateSch
from typing import List
from uuid import UUID
from datetime import datetime
from sqlalchemy import exc


class CRUDKjbRekening(CRUDBase[KjbRekening, KjbRekeningCreateSch, KjbRekeningUpdateSch]):
    pass

kjb_rekening = CRUDKjbRekening(KjbRekening)