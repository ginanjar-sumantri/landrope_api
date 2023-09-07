from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.draft_report_map_model import DraftReportMap
from schemas.draft_report_map_sch import DraftReportMapCreateSch, DraftReportMapUpdateSch
from typing import List
from uuid import UUID

class CRUDDraftReportMap(CRUDBase[DraftReportMap, DraftReportMapCreateSch, DraftReportMapUpdateSch]):
    async def get_multi_by_report_id(
            self, 
            *,
            report_id:UUID,
            db_session : AsyncSession | None = None, 
            query : DraftReportMap | Select[DraftReportMap]| None = None
            ) -> List[DraftReportMap] | None:
        
        db_session = db_session or db.session
        if query is None:
            query = select(self.model).where(self.model.report_id == report_id)

        response =  await db_session.execute(query)
        return response.scalars().all()
    
    async def get_not_in_by_ids_and_report_id(
            self, 
            *, 
            list_ids: List[UUID | str],
            report_id:UUID,
            db_session : AsyncSession | None = None
            ) -> List[DraftReportMap] | None:
    
        db_session = db_session or db.session
        query = select(self.model
                       ).where(
                           and_(
                               ~self.model.id.in_(list_ids), 
                               self.model.report_id == report_id
                               )
                            )
        
        response =  await db_session.execute(query)
        return response.scalars().all()

draft_report_map = CRUDDraftReportMap(DraftReportMap)