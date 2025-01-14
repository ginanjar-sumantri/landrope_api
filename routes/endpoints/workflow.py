from uuid import UUID
from fastapi import APIRouter, status, Depends, HTTPException, Request
from fastapi_pagination import Params
from fastapi_async_sqlalchemy import db
from sqlmodel import delete
from models.workflow_model import Workflow
from models.worker_model import Worker
from schemas.workflow_sch import WorkflowSystemCallbackSch, WorkflowUpdateSch, WorkflowCreateSch
from schemas.workflow_history_sch import WorkflowHistoryCreateSch
from schemas.workflow_next_approver_sch import WorkflowNextApproverCreateSch
from schemas.response_sch import (PostResponseBaseSch, GetResponseBaseSch, DeleteResponseBaseSch, GetResponsePaginatedSch, PutResponseBaseSch, create_response)
from services.helper_service import HelperService
from services.signature_service import SignatureService
from services.gcloud_task_service import GCloudTaskService
from configs.config import settings
from common.exceptions import (IdNotFoundException, ImportFailedException)
from common.generator import generate_code
from common.enum import WorkflowLastStatusEnum, WorkflowEntityEnum
from models.code_counter_model import CodeCounterEnum
from datetime import datetime
import crud
import json

router = APIRouter()

@router.post("/notification")
async def notification(payload: dict, request:Request):
    
    """Notification Workflow"""
    try:
        db_session = db.session

        signature = request.headers.get("Signature", None)
        verify = SignatureService().verify_signature_request(msg=payload, signature=signature, client_public_key=settings.WF_PUBLIC_KEY)

        if verify == False:
            raise HTTPException(status_code=401, detail="Signature not authorize!")

        sch = WorkflowSystemCallbackSch(**payload)

        obj_current = await crud.workflow.get_by_reference_id(reference_id=sch.client_reff_no)
        if obj_current is None:
            raise HTTPException(status_code=422, detail="Client Reff No not found")
        
        await crud.workflow_next_approver.delete_by_workflow_id(workflow_id=obj_current.id, db_session=db_session, with_commit=False)
        
        obj_new = WorkflowUpdateSch(reference_id=obj_current.reference_id,
                                    txn_id=sch.txn_id,
                                    entity=obj_current.entity, 
                                    flow_id=obj_current.flow_id,
                                    step_name=sch.step_name,
                                    last_status=sch.last_status_enum,
                                    last_status_at=HelperService().no_timezone(sch.last_status_at),
                                    last_step_app_email= sch.last_step_approver.email if sch.last_step_approver else None,
                                    last_step_app_name=sch.last_step_approver.name if sch.last_step_approver else None,
                                    last_step_app_action=sch.last_step_approver.status if sch.last_step_approver else None,
                                    last_step_app_action_at=HelperService().no_timezone(sch.last_step_approver.confirm_at) if sch.last_step_approver else None,
                                    last_step_app_action_remarks=sch.last_step_approver.confirm_remarks if sch.last_step_approver else None,
                                    version=obj_current.version
                                    )

        obj_updated = await crud.workflow.update(obj_current=obj_current, obj_new=obj_new, db_session=db_session, with_commit=False)

        if sch.next_approver is not None:
            for next_approver in sch.next_approver:
                obj_next_approver_new = WorkflowNextApproverCreateSch(**next_approver.dict(), workflow_id=obj_updated.id)
                await crud.workflow_next_approver.create(obj_in=obj_next_approver_new, created_by_id=obj_updated.updated_by_id, db_session=db_session, with_commit=False)

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

        if obj_updated.entity == WorkflowEntityEnum.KJB and obj_updated.last_status == WorkflowLastStatusEnum.COMPLETED:
            url = f'{request.base_url}landrope/kjbhd/task/update-to-bidang'
            GCloudTaskService().create_task(payload={"id":str(obj_updated.reference_id)}, base_url=url)

            url2 = f'{request.base_url}landrope/kjbhd/task/update-to-alashak-bundle'
            GCloudTaskService().create_task(payload={"id":str(obj_updated.reference_id)}, base_url=url2)

        # if obj_updated.entity == WorkflowEntityEnum.TERMIN and obj_updated.last_status == WorkflowLastStatusEnum.COMPLETED:
        #     url = f'{request.base_url}landrope/termin/task/create_rfp'
        #     GCloudTaskService().create_task(payload={"id": str(obj_updated.reference_id)}, base_url=url)
        
        return {"success" : True}
    
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))