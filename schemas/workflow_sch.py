from models.workflow_model import Workflow, WorkflowBase, WorkflowFullBase
from common.partial import optional
from common.enum import WorkflowLastStatusEnum
from sqlmodel import SQLModel, Field
from datetime import date, datetime
from configs.config import settings

class WorkflowCreateSch(WorkflowBase):
    pass

class WorkflowSch(WorkflowFullBase):
    pass

@optional
class WorkflowUpdateSch(WorkflowBase):
    pass

class WorkflowSystemAttachment(SQLModel):
    name:str
    url:str

class WorkflowSystemCreateSch(SQLModel):
    client_id:str | None = Field(default=settings.WF_CLIENT_ID)
    client_ref_no:str | None
    flow_id :str | None
    additional_info:dict
    descs:str | None
    attachments:list[WorkflowSystemAttachment]


class WorkflowCreateResponseSch(SQLModel):
    client_ref_no:str
    id:str
    last_status:WorkflowLastStatusEnum|None
    updated_at:datetime