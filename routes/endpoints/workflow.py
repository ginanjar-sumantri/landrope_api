from uuid import UUID
from fastapi import APIRouter, status, Depends, HTTPException
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from models.workflow_model import Workflow
from models.worker_model import Worker
from schemas.workflow_sch import WorkflowSystemCallbackSch, WorkflowUpdateSch, WorkflowCreateSch
from schemas.workflow_history_sch import WorkflowHistoryCreateSch
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from services.helper_service import HelperService
from common.exceptions import (IdNotFoundException, ImportFailedException)
from common.generator import generate_code
from common.enum import WorkflowLastStatusEnum
from models.code_counter_model import CodeCounterEnum
from datetime import datetime
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
        
        obj_new = WorkflowUpdateSch(reference_id=obj_current.reference_id,
                                    entity=obj_current.entity, 
                                    flow_id=obj_current.flow_id,
                                    step_name=sch.step_name,
                                    last_status=sch.last_status_enum,
                                    last_status_at=HelperService().no_timezone(sch.last_status_at),
                                    last_step_app_email= sch.last_step_approver.email if sch.last_step_approver else None,
                                    last_step_app_name=sch.last_step_approver.name if sch.last_step_approver else None,
                                    last_step_app_action=sch.last_step_approver.status if sch.last_step_approver else None,
                                    last_step_app_action_at=HelperService().no_timezone(sch.last_step_approver.confirm_at) if sch.last_step_approver else None,
                                    last_step_app_action_remarks=sch.last_step_approver.confirm_remarks if sch.last_step_approver else None
                                    )

        obj_updated = await crud.workflow.update(obj_current=obj_current, obj_new=obj_new, db_session=db_session, with_commit=False)

        obj_in = WorkflowHistoryCreateSch(
            workflow_id=obj_updated.id,
            step_name=sch.step_name,
            last_status=sch.last_status_enum,
            last_status_at=HelperService().no_timezone(sch.last_status_at),
            last_step_app_email= sch.last_step_approver.email if sch.last_step_approver else None,
            last_step_app_name=sch.last_step_approver.name if sch.last_step_approver else None,
            last_step_app_action=sch.last_step_approver.status if sch.last_step_approver else None,
            last_step_app_action_at=HelperService().no_timezone(sch.last_step_approver.confirm_at) if sch.last_step_approver else None,
            last_step_app_action_remarks=sch.last_step_approver.confirm_remarks if sch.last_step_approver else None
        )


        await crud.workflow_history.create(obj_in=obj_in, db_session=db_session)
        
        return {"success" : True}
    
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))