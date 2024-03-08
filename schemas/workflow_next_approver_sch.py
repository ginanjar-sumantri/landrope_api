from models.workflow_model import WorkflowNextApprover, WorkflowNextApproverBase, WorkflowNextApproverFullBase
from common.partial import optional
from sqlmodel import SQLModel, Field
from datetime import date, datetime

class WorkflowNextApproverCreateSch(WorkflowNextApproverBase):
    pass

class WorkflowNextApproverSch(WorkflowNextApproverFullBase):
    pass

@optional
class WorkflowNextApproverUpdateSch(WorkflowNextApproverBase):
    pass