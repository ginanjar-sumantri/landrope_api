from models.workflow_model import WorkflowHistory, WorkflowHistoryBase, WorkflowHistoryFullBase
from common.partial import optional
from sqlmodel import SQLModel, Field
from datetime import date, datetime

class WorkflowHistoryCreateSch(WorkflowHistoryBase):
    pass

class WorkflowHistorySch(WorkflowHistoryFullBase):
    pass

@optional
class WorkflowHistoryUpdateSch(WorkflowHistoryBase):
    pass