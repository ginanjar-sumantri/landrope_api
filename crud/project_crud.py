from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from typing import List
from crud.base_crud import CRUDBase
from models.project_model import Project
from schemas.project_sch import ProjectCreateSch, ProjectUpdateSch
from uuid import UUID

class CRUDProject(CRUDBase[Project, ProjectCreateSch, ProjectUpdateSch]):
    async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> Project | None:
        
        db_session = db_session or db.session
        
        query = select(Project).where(Project.id == id
                                        ).options(selectinload(Project.section)
                                        ).options(selectinload(Project.main_project))
        
        response = await db_session.execute(query)

        return response.scalar_one_or_none()

    async def get_by_name(
        self, *, name: str, db_session: AsyncSession | None = None
    ) -> Project | None:
        db_session = db_session or db.session
        query = select(self.model).options(selectinload(Project.section)
                                ).options(selectinload(Project.main_project)
                                ).where(func.lower(func.trim(func.replace(self.model.name, ' ', ''))) == name.strip().lower().replace(' ', ''))
        
        obj = await db_session.execute(query)
        return obj.scalar_one_or_none()
    
    async def get_all_project_tree_report_map(
            self, 
            *,
            db_session : AsyncSession | None = None
            ):
        
        db_session = db_session or db.session
        
        query = select(Project.id,
                       Project.name).select_from(Project)

        response =  await db_session.execute(query)
        return response.fetchall()

project = CRUDProject(Project)