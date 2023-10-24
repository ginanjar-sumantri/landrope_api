from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy.orm import selectinload
from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.skpt_model import Skpt, SkptDt
from models.planing_model import Planing
from models.project_model import Project
from schemas.skpt_dt_sch import SkptDtCreateSch, SkptDtUpdateSch
from uuid import UUID


class CRUDSkptDt(CRUDBase[SkptDt, SkptDtCreateSch, SkptDtUpdateSch]):
    async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> SkptDt | None:
        
        db_session = db_session or db.session
        
        query = select(SkptDt).where(SkptDt.id == id
                                        ).options(selectinload(SkptDt.skpt
                                                            ).options(selectinload(Skpt.ptsk)
                                                            )
                                        ).options(selectinload(SkptDt.planing
                                                            ).options(selectinload(Planing.project
                                                                                ).options(selectinload(Project.section))
                                                            ).options(selectinload(Planing.desa)
                                                            )
                                        )
        
        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
    async def get_by_skpt_id_and_planing_id(self, *, skpt_id: UUID | str, planing_id: UUID | str, db_session: AsyncSession | None = None) -> SkptDt | None:
        db_session = db_session or db.session
        query = select(self.model).where(and_(self.model.skpt_id == skpt_id, self.model.planing_id == planing_id)).limit(1)
        response = await db_session.execute(query)

        return response.scalar_one_or_none()


skptdt = CRUDSkptDt(SkptDt)