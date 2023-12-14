from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy.orm import selectinload
from common.ordered import OrderEnumSch
from common.enum import WorkflowEntityEnum
from crud.base_crud import CRUDBase
from models.workflow_model import WorkflowTemplate
from schemas.workflow_template_sch import WorkflowTemplateCreateSch, WorkflowTemplateUpdateSch
from typing import List
from uuid import UUID

class CRUDWorkflowTemplate(CRUDBase[WorkflowTemplate, WorkflowTemplateCreateSch, WorkflowTemplateUpdateSch]):
    async def get_by_entity(self, 
                  *, 
                  entity: WorkflowEntityEnum | None = None,
                  query : WorkflowTemplate | Select[WorkflowTemplate] | None = None,
                  db_session: AsyncSession | None = None
                  ) -> WorkflowTemplate | None:
        
        db_session = db_session or db.session

        if query == None:
            query = select(self.model).where(self.model.entity == entity)

        response = await db_session.execute(query)

        return response.scalar_one_or_none()

workflow_template = CRUDWorkflowTemplate(WorkflowTemplate)