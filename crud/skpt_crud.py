from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch

from crud.base_crud import CRUDBase
from models.skpt_model import Skpt
from models.ptsk_model import Ptsk
from schemas.skpt_sch import SkptCreateSch, SkptUpdateSch

class CRUDSKPT(CRUDBase[Skpt, SkptCreateSch, SkptUpdateSch]):
    async def get_by_sk_number(
        self, *, number: str, db_session: AsyncSession | None = None
    ) -> Skpt:
        db_session = db_session or db.session
        obj = await db_session.execute(select(Skpt).where(Skpt.nomor_sk == number))
        return obj.scalar_one_or_none()
    

skpt = CRUDSKPT(Skpt)