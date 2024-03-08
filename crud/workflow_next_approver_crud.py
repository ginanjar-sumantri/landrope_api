from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy import exc
from sqlalchemy.orm import selectinload
from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.workflow_model import WorkflowNextApprover
from schemas.workflow_next_approver_sch import WorkflowNextApproverCreateSch, WorkflowNextApproverUpdateSch
from typing import List
from uuid import UUID

class CRUDWorkflowNextApprover(CRUDBase[WorkflowNextApprover, WorkflowNextApproverCreateSch, WorkflowNextApproverUpdateSch]):
    async def delete_by_workflow_id(
            self, 
            *, 
            workflow_id:UUID,
            query: WorkflowNextApprover | None = None,
            db_session : AsyncSession | None = None,
            with_commit:bool | None = True
            ) -> bool:
        
        db_session = db_session or db.session
        if query is None:
            query = self.model.__table__.delete().where(self.model.workflow_id == workflow_id)

        try:
            await db_session.execute(query)
            if with_commit:
                await db_session.commit()
        except exc.IntegrityError:
            db_session.rollback()
            raise HTTPException(status_code=422, detail="failed delete data")

        return True

workflow_next_approver = CRUDWorkflowNextApprover(WorkflowNextApprover)