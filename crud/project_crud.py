from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from crud.base_crud import CRUDBase
from models.project_model import Project
from schemas.project_sch import ProjectCreateSch, ProjectUpdateSch

class CRUDProject(CRUDBase[Project, ProjectCreateSch, ProjectUpdateSch]):
    pass

project = CRUDProject(Project)