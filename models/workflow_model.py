from sqlmodel import SQLModel, Field, Relationship
from common.enum import WorkflowLastStatusEnum, WorkflowEntityEnum
from models.base_model import BaseUUIDModel
from uuid import UUID
from datetime import datetime
from pydantic import EmailStr

class WorkflowBase(SQLModel):
    reference_id:UUID = Field(nullable=False) #id object (spk, memo tanah dll)
    step_name:str | None = Field(nullable=True)
    last_status:WorkflowLastStatusEnum|None = Field(nullable=True)
    last_status_at:datetime|None = Field(nullable=True)
    last_step_app_email:str|None = Field(nullable=True)
    last_step_app_name:str|None = Field(nullable=True)
    last_step_app_action:str|None = Field(nullable=True)
    last_step_app_action_at:datetime|None = Field(nullable=True)
    last_step_app_action_remarks:str|None = Field(nullable=True)
    entity:WorkflowEntityEnum|None = Field(nullable=False)
    flow_id:str|None = Field(nullable=False)
    version:int|None = Field(default=1)

class WorkflowFullBase(BaseUUIDModel, WorkflowBase):
    pass

class Workflow(WorkflowFullBase, table=True):
    workflow_histories:list["WorkflowHistory"] = Relationship(
        sa_relationship_kwargs=
        {
            "lazy":"select"
        },
        back_populates="workflow"
    )

    workflow_next_approvers:list["WorkflowNextApprover"] = Relationship(
        sa_relationship_kwargs=
        {
            "lazy":"select"
        },
        back_populates="workflow"
    )

class WorkflowNextApproverBase(SQLModel):
    workflow_id: UUID = Field(nullable=False, foreign_key="workflow.id")
    email: EmailStr | None = Field(nullable=True)
    name: str | None = Field(nullable=True)

class WorkflowNextApproverFullBase(BaseUUIDModel, WorkflowNextApproverBase):
    pass

class WorkflowNextApprover(WorkflowNextApproverFullBase, table=True):
    workflow:"Workflow" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy":"select"
        },
        back_populates="workflow_next_approvers"
    )

class WorkflowHistoryBase(SQLModel):
    workflow_id:UUID|None = Field(foreign_key="workflow.id", nullable=False)
    step_name:str | None = Field(nullable=True)
    last_status:WorkflowLastStatusEnum|None = Field(nullable=True)
    last_status_at:datetime|None = Field(nullable=True)
    last_step_app_email:str|None = Field(nullable=True)
    last_step_app_name:str|None = Field(nullable=True)
    last_step_app_action:str|None = Field(nullable=True)
    last_step_app_action_at:datetime|None = Field(nullable=True)
    last_step_app_action_remarks:str|None = Field(nullable=True)

class WorkflowHistoryFullBase(BaseUUIDModel, WorkflowHistoryBase):
    pass

class WorkflowHistory(WorkflowHistoryFullBase, table=True):
    workflow:"Workflow" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy":"select"
        },
        back_populates="workflow_histories"
    )

class WorkflowTemplateBase(SQLModel):
    entity:WorkflowEntityEnum | None
    flow_id:str | None

class WorkflowTemplateFullBase(WorkflowTemplateBase, BaseUUIDModel):
    pass

class WorkflowTemplate(WorkflowTemplateFullBase, table=True):
    pass
