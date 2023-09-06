from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from sqlalchemy import exc
from sqlmodel import select, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from crud.base_crud import CRUDBase
from models.desa_model import Desa
from models.planing_model import Planing
from models.project_model import Project
from models.code_counter_model import CodeCounterEnum
from schemas.desa_sch import DesaCreateSch, DesaUpdateSch, DesaSch
from common.generator import generate_code
from typing import List
from uuid import UUID

from datetime import datetime

class CRUDDesa(CRUDBase[Desa, DesaCreateSch, DesaUpdateSch]):
    async def get_all_ptsk_tree_report_map(
            self, 
            *,
            project_id:UUID,
            db_session : AsyncSession | None = None
            ):
        
        db_session = db_session or db.session
        
        query = select(Desa.id,
                       Desa.name,
                       Project.id.label("project_id"),
                       Project.name.label("project_name")).select_from(Desa
                                    ).join(Planing, Desa.id == Planing.desa_id,
                                    ).join(Project, Project.id == Planing.project_id
                                    ).where(Project.id == project_id)

        response =  await db_session.execute(query)
        return response.fetchall()

    
desa = CRUDDesa(Desa)