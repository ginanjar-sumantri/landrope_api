from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy.orm import selectinload
from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models import SubProject
from schemas.sub_project_sch import SubProjectCreateSch, SubProjectUpdateSch
from typing import List
from uuid import UUID
from datetime import datetime
from sqlalchemy import exc


class CRUDSubProject(CRUDBase[SubProject, SubProjectCreateSch, SubProjectUpdateSch]):
    async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> SubProject | None:
        
        db_session = db_session or db.session
        
        query = select(SubProject).where(SubProject.id == id
                                        ).options(selectinload(SubProject.project)
                                        ).options(selectinload(SubProject.main_project))
        
        response = await db_session.execute(query)

        return response.scalar_one_or_none()

sub_project = CRUDSubProject(SubProject)