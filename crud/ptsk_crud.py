from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.ptsk_model import Ptsk
from models.skpt_model import Skpt, SkptDt
from models.desa_model import Desa
from models.project_model import Project
from models.planing_model import Planing
from schemas.ptsk_sch import PtskCreateSch, PtskUpdateSch
from uuid import UUID

class CRUDPTSK(CRUDBase[Ptsk, PtskCreateSch, PtskUpdateSch]):
    
    async def get_filtered_ptsk(
        self,
        *,
        keyword:str | None = None,
        params: Params | None = Params(),
        order_by: str | None = None,
        order: OrderEnumSch | None = OrderEnumSch.ascendent,
        query: Ptsk | Select[Ptsk] | None = None,
        db_session: AsyncSession | None = None,
    ) -> Page[Ptsk]:
        db_session = db_session or db.session

        columns = self.model.__table__.columns

        # if order_by not in columns or order_by is None:
        #     order_by = self.model.id

        find = False
        for c in columns:
            if c.name == order_by:
                find = True
                break
        
        if order_by is None or find == False:
            order_by = "id"

        if query is None:
            if order == OrderEnumSch.ascendent:
                if keyword is None:
                    query = select(self.model).order_by(columns[order_by].asc())
                else:
                    query = select(self.model).filter(or_(self.model.name.ilike(f'%{keyword}%'),
                                                          self.model.code.ilike(f'%{keyword}%')
                                                          )).order_by(columns[order_by].asc())
            else:
                if keyword is None:
                    query = select(self.model).order_by(columns[order_by].desc())
                else:
                    query = select(self.model).filter(or_(self.model.name.ilike(f'%{keyword}%'),
                                                          self.model.code.ilike(f'%{keyword}%')
                                                         )).order_by(columns[order_by].desc())
            
        return await paginate(db_session, query, params)
    
    async def get_all_ptsk_tree_report_map(
            self, 
            *,
            project_id:UUID,
            desa_id:UUID,
            db_session : AsyncSession | None = None
            ):
        
        db_session = db_session or db.session
        
        query = select(Ptsk.id,
                       Ptsk.name,
                       Desa.id.label("desa_id"),
                       Desa.name.label("desa_name"),
                       Project.id.label("project_id"),
                       Project.name.label("project_name")).select_from(Ptsk
                                    ).join(Skpt, Ptsk.id == Skpt.ptsk_id,
                                    ).join(SkptDt, Skpt.id == SkptDt.skpt_id,
                                    ).join(Planing, Planing.id == SkptDt.planing_id,
                                    ).join(Desa, Desa.id == Planing.desa_id,
                                    ).join(Project, Project.id == Planing.project_id
                                    ).where(
                                        and_(
                                                Project.id == project_id,
                                                Desa.id == desa_id
                                            )).distinct()

        response =  await db_session.execute(query)
        return response.fetchall()

ptsk = CRUDPTSK(Ptsk)