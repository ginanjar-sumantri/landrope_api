from uuid import UUID
from fastapi import APIRouter, status, Depends, HTTPException
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from models.dokumen_model import Dokumen
from models.worker_model import Worker
from schemas.workflow_sch import WorkflowSystemCallbackSch, WorkflowUpdateSch, WorkflowCreateSch
from schemas.workflow_history_sch import WorkflowHistoryCreateSch
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from common.exceptions import (IdNotFoundException, ImportFailedException)
from common.generator import generate_code
from models.code_counter_model import CodeCounterEnum
import crud

router = APIRouter()

@router.post("/notification")
async def notification(
            sch: WorkflowSystemCallbackSch):
    
    """Create a new object"""
    try:
        db_session = db.session

        obj_current = await crud.workflow.get_by_reference_id(reference_id=sch.client_reff_no)
        if obj_current is None:
            raise HTTPException(status_code=422, detail="Client Reff No not found")
        
        obj_new = WorkflowUpdateSch.from_orm(obj_current)
        obj_new.step_name = sch.step_name
        obj_new.last_status = sch.last_status_enum,
        obj_new.last_status_at = sch.last_status_at,
        obj_new.last_step_app_email = sch.last_step_approver.email,
        obj_new.last_step_app_name = sch.last_step_approver.name,
        obj_new.last_step_app_action = sch.last_step_approver.status,
        obj_new.last_step_app_action_at = sch.last_step_approver.confirm_at,
        obj_new.last_step_app_action_remarks = sch.last_step_approver.confirm_remarks

        obj_updated = await crud.workflow.update(obj_current=obj_current, obj_new=obj_new, db_session=db_session, with_commit=False)

        obj_in = WorkflowHistoryCreateSch.from_orm(obj_updated)
        obj_in.workflow_id = obj_updated.id

        await crud.workflow_history.create(obj_in=obj_in, db_session=db_session)
        
        return {"success" : True}
    
    except Exception as e:
        raise HTTPException(status_code=422, detail="Failed notification Client")