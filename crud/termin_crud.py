from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.termin_model import Termin
from models.invoice_model import Invoice
from models.tahap_model import Tahap
from models.kjb_model import KjbHd
from models.spk_model import Spk
from models.bidang_model import Bidang
from schemas.termin_sch import TerminCreateSch, TerminUpdateSch
from typing import List
from uuid import UUID

class CRUDTermin(CRUDBase[Termin, TerminCreateSch, TerminUpdateSch]):
    pass

termin = CRUDTermin(Termin)