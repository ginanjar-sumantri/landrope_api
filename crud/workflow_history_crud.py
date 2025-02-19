from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from sqlalchemy.orm import selectinload
from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.workflow_model import WorkflowHistory
from schemas.workflow_history_sch import WorkflowHistoryCreateSch, WorkflowHistoryUpdateSch
from typing import List
from uuid import UUID

class CRUDWorkflowHistory(CRUDBase[WorkflowHistory, WorkflowHistoryCreateSch, WorkflowHistoryUpdateSch]):
    pass

workflow_history = CRUDWorkflowHistory(WorkflowHistory)