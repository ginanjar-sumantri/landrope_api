from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List
from crud.base_crud import CRUDBase
from models.project_model import Project
from schemas.project_sch import ProjectCreateSch, ProjectUpdateSch

class CRUDProject(CRUDBase[Project, ProjectCreateSch, ProjectUpdateSch]):
    async def get_by_name(
        self, *, name: str, db_session: AsyncSession | None = None
    ) -> ProjectCreateSch:
        db_session = db_session or db.session
        obj = await db_session.execute(select(Project).where(Project.name == name))
        return obj.scalar_one_or_none()
    
    async def get_by_names(self, *, list_names: List[str], db_session : AsyncSession | None = None) -> List[ProjectCreateSch] | None:
        db_session = db_session or db.session
        query = select(self.model).where(self.model.name.in_(list_names))
        response =  await db_session.execute(query)
        return response.scalars().all()

project = CRUDProject(Project)