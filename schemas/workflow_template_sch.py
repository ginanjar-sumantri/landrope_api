from models.workflow_model import WorkflowTemplate, WorkflowTemplateBase, WorkflowTemplateFullBase
from common.partial import optional
from sqlmodel import SQLModel, Field
from datetime import date, datetime

class WorkflowTemplateCreateSch(WorkflowTemplateBase):
    pass

class WorkflowTemplateSch(WorkflowTemplateFullBase):
    pass

@optional
class WorkflowTemplateUpdateSch(WorkflowTemplateBase):
    pass