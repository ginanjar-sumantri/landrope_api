from models.workflow_model import Workflow, WorkflowBase, WorkflowFullBase
from common.partial import optional
from common.enum import WorkflowLastStatusEnum
from sqlmodel import SQLModel, Field
from datetime import date, datetime
from configs.config import settings
from typing import Dict

class WorkflowCreateSch(WorkflowBase):
    pass

class WorkflowSch(WorkflowFullBase):
    pass

@optional
class WorkflowUpdateSch(WorkflowBase):
    pass

class WorkflowSystemAttachmentSch(SQLModel):
    name:str
    url:str

class WorkflowSystemCreateSch(SQLModel):
    client_id:str | None = Field(default=settings.WF_CLIENT_ID)
    client_ref_no:str | None
    flow_id :str | None
    additional_info:dict|None = Field(default={})
    descs:str | None
    attachments:list[Dict]
    version:int | None = Field(default=1)


class WorkflowCreateResponseSch(SQLModel):
    client_ref_no:str
    id:str
    last_status:WorkflowLastStatusEnum|None
    updated_at:datetime

class WorkflowSystemApproverSch(SQLModel):
    email: str|None
    name: str|None
    status: str|None
    confirm_at: datetime|None
    confirm_remarks: str|None

class WorkflowSystemNextApproverSch(SQLModel):
    email: str|None
    name: str|None

class WorkflowSystemCallbackSch(SQLModel):
    client_reff_no:str|None
    txn_id: str|None
    last_status_enum:str|None
    step_name: str|None
    last_status_at: datetime|None
    last_step_approver: WorkflowSystemApproverSch|None
    next_approver: list[WorkflowSystemNextApproverSch]|None