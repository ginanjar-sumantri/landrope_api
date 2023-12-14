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
from models.workflow_model import Workflow, WorkflowHistory
from schemas.workflow_sch import WorkflowCreateSch, WorkflowUpdateSch, WorkflowSystemCreateSch
from services.workflow_service import WorkflowService
from configs.config import settings
from typing import List
from uuid import UUID
from datetime import datetime

class CRUDWorkflow(CRUDBase[Workflow, WorkflowCreateSch, WorkflowUpdateSch]):
    async def create_(self, *, 
                     obj_in: WorkflowCreateSch | Workflow, 
                     obj_wf: WorkflowSystemCreateSch,
                     created_by_id : UUID | str | None = None, 
                     db_session : AsyncSession | None = None,
                     with_commit: bool | None = True) -> Workflow :
        db_session = db_session or db.session

        body = vars(obj_wf)

        response, msg = await WorkflowService().create_workflow(body=body)

        if response is None:
            raise HTTPException(status_code=422, detail=f"Failed to connect workflow system. Detail : {msg}")

        db_obj = self.model.from_orm(obj_in) #type ignore
        db_obj.created_at = datetime.utcnow()
        db_obj.updated_at = datetime.utcnow()
        if created_by_id:
            db_obj.created_by_id = created_by_id
            db_obj.updated_by_id = created_by_id
        
        try:
            db_session.add(db_obj)
            if with_commit:
                await db_session.commit()
        except exc.IntegrityError:
            await db_session.rollback()
            raise HTTPException(status_code=409, detail="Resource already exists")
        
        if with_commit:
            await db_session.refresh(db_obj)
        return db_obj
    
    async def get_by_reference_id(self, 
                  *, 
                  reference_id: UUID | str | None = None,
                  query : Workflow | Select[Workflow] | None = None,
                  db_session: AsyncSession | None = None
                  ) -> Workflow | None:
        
        db_session = db_session or db.session

        if query == None:
            query = select(self.model).where(self.model.reference_id == reference_id)

        response = await db_session.execute(query)

        return response.scalar_one_or_none()

workflow = CRUDWorkflow(Workflow)