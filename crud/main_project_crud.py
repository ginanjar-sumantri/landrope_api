from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models import MainProject
from schemas.main_project_sch import MainProjectCreateSch, MainProjectUpdateSch
from typing import List
from uuid import UUID
from datetime import datetime
from sqlalchemy import exc


class CRUDMainProject(CRUDBase[MainProject, MainProjectCreateSch, MainProjectUpdateSch]):
    pass

main_project = CRUDMainProject(MainProject)